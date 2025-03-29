
from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader
from surrealdb import AsyncSurreal
import datetime
from surrealdb_rag.ux_helpers import *

CORPUS_TABLE_SELECT = """
        SELECT 
            display_name,table_name,embed_models,additional_data_keys,corpus_graph_tables,
            fn::get_datetime_range_for_corpus_table(corpus_graph_tables.relation_table_name,corpus_graph_tables.relation_date_field)
            AS corpus_graph_tables.date_range
        FROM (
            SELECT

            display_name,table_name,embed_models,fn::additional_data_keys(table_name) as additional_data_keys,
                type::thing('corpus_graph_tables',table_name).{
                    entity_date_field,entity_display_name,entity_table_name,
                    relation_date_field,relation_display_name,relation_table_name,
                    source_document_display_name,source_document_table_name,
                    } as corpus_graph_tables
                FROM corpus_table FETCH embed_models,embed_models.model
            );
        """

"""
Handles the retrieval of available LLM models and corpus tables.
"""


class CorpusTableListHandler():
    """
        Initializes the ModelListHandler.

        Args:
            model_params (ModelParams): Model parameters.
            connection (AsyncSurreal): Asynchronous SurrealDB connection.
        """
    def __init__(self, connection):
        self.CORPUS_TABLES = {}
        self.connection = connection
    
    

    def populate_corpus_tables(self,corpus_tables):
        # Filter out OpenAI models if API key is absent
        for corpus_table in corpus_tables:
            
            # create an dict item for table_name
            table_name = corpus_table["table_name"]
            self.CORPUS_TABLES[table_name] = {}
            self.CORPUS_TABLES[table_name]["display_name"] = corpus_table["display_name"]
            self.CORPUS_TABLES[table_name]["table_name"] = corpus_table["table_name"]
            self.CORPUS_TABLES[table_name]["additional_data_keys"] = corpus_table["additional_data_keys"]
            self.CORPUS_TABLES[table_name]["embed_models"] = []
            self.CORPUS_TABLES[table_name]["corpus_graph_tables"] = corpus_table["corpus_graph_tables"]
            #datetime not serializable
            if corpus_table["corpus_graph_tables"] and corpus_table["corpus_graph_tables"]["date_range"]:
                self.CORPUS_TABLES[table_name]["corpus_graph_tables"]["date_range"]["min"] = str(corpus_table["corpus_graph_tables"]["date_range"]["min"])
                self.CORPUS_TABLES[table_name]["corpus_graph_tables"]["date_range"]["max"] = str(corpus_table["corpus_graph_tables"]["date_range"]["max"])

            for model in corpus_table["embed_models"]:
                model_def =  model["model"]
                model_def_id = model_def["id"].id
                if model_def_id[0] != "OPENAI" or (
                    model_def_id[0] == "OPENAI" and self.model_params.openai_token):

                    self.CORPUS_TABLES[table_name]["embed_models"].append(
                            {"model":model_def_id,
                                "field_name":model["field_name"],
                                "corpus":model_def["corpus"],
                                "description":model_def["description"],
                                "host":model_def["host"],
                                "model_trainer":model_def["model_trainer"],
                                "version":model_def["version"],
                                "dimensions":model_def["dimensions"],
                                }
                        )
        return self.CORPUS_TABLES 


    
    """
    Retrieves a dictionary of available corpus tables.

    Returns:
        dict: Dictionary of available corpus tables.
    """
    async def available_corpus_tables(self):
        if self.CORPUS_TABLES != {}:
            return self.CORPUS_TABLES 
        else:
            self.CORPUS_TABLES = {}
            corpus_tables = await self.connection.query(CORPUS_TABLE_SELECT)
            return self.populate_corpus_tables(corpus_tables)


            
    def available_corpus_tables_sync(self):
        """
        Synchronous version of available_corpus_tables.
        """
        if self.CORPUS_TABLES != {}:
            return self.CORPUS_TABLES 
        else:
            self.CORPUS_TABLES = {}
            corpus_tables = self.connection.query(CORPUS_TABLE_SELECT)
            return self.populate_corpus_tables(corpus_tables)



        
class CorpusDataHandler():



    GEMINI_CHAT_COMPLETE = """RETURN fn::gemini_chat_complete($llm,$prompt_with_context,$input,$google_token);"""

    OPENAI_CHAT_COMPLETE = """RETURN fn::openai_chat_complete($llm,$prompt_with_context, $input, $temperature, $openai_token);"""


    """
    Initializes the RAGChatHandler.

    Args:
        model_data (str): Model data.
        model_params (ModelParams): Model parameters.
        connection (AsyncSurreal): Asynchronous SurrealDB connection.
    """
    def __init__(self,connection:AsyncSurreal,corpus_table_info:dict):
        
        self.connection = connection
        self.corpus_table_info = corpus_table_info

    async def query_additional_data(self,additional_data_field:str):
        return await self.connection.query(
                """RETURN fn::select_additional_data($corpus_table,$key)""",params = {"corpus_table":self.corpus_table_info["table_name"],"key":additional_data_field}    
            )
    


    async def relation_detail(self,corpus_table_detail:dict,identifier_in:str,identifier_out:str,relationship:str):
        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")
        relation_info = await self.connection.query(
                """
        RETURN array::group(
        SELECT in.{
            additional_data,
            entity_type,
            identifier,
            name}
        ,out.{
            additional_data,
            entity_type,
            identifier,
            name},relationship,source_document.{additional_data,title,url},contexts,confidence FROM type::table($relation_table_name) 
        WHERE in.identifier=$identifier_in AND out.identifier=$identifier_out and relationship = $relationship);
                        """,
                params = {"relation_table_name":corpus_graph_tables.get("relation_table_name"),"identifier_in":identifier_in,"identifier_out":identifier_out,"relationship":relationship} 
            )
        return relation_info



    async def entity_detail(self,corpus_table_detail:dict,identifier:str):
        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")
        
        entity_relations = await self.connection.query(
            """
                RETURN array::group(
                SELECT VALUE <->?.{confidence,contexts,relationship,source_document.{url,title},
                    in.{entity_type, identifier, name},
                    out.{entity_type, identifier, name}} 
                FROM type::table($entity_table_name) WHERE identifier=$identifier);
                    """,
            params = {"entity_table_name":corpus_graph_tables.get("entity_table_name"),"identifier":identifier} 
        )

        entity_relations_dict = organize_relations_for_ux(entity_relations,identifier)

        entity_mentions = await self.connection.query("""
            RETURN array::group (
                SELECT VALUE {"source_document":source_document,"contexts":contexts,"additional_data":additional_data}
                    FROM  type::table($entity_table_name) WHERE identifier = $identifier FETCH source_document
                )
            ;""",
            params = {"entity_table_name":corpus_graph_tables.get("entity_table_name"),"identifier":identifier} 
        )

        entity_info = await self.connection.query("""
            SELECT name,identifier,entity_type FROM type::table($entity_table_name) WHERE identifier = $identifier LIMIT 1
            ;""",
            params = {"entity_table_name":corpus_graph_tables.get("entity_table_name"),"identifier":identifier} 
        )
        
        return {
            "entity_relations":list(entity_relations_dict.values()),
            "entity_mentions":entity_mentions,
            "entity_info":entity_info[0]
        }
    


    async def source_document_details(self,corpus_table_detail:dict,url:str):
        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")

        url = unformat_url_id(url)

        source_document_info = await self.connection.query(
            """SELECT additional_data,title,url FROM type::thing($source_document_table_name,$url);""",
            params = {"source_document_table_name":corpus_graph_tables.get("source_document_table_name"),"url":url}    
        )
        entities = await self.connection.query(
            f"""SELECT * FROM {corpus_graph_tables.get("entity_table_name")}:[$url,None,None]..[$url,..,..];""",
            params = {"source_document_table_name":corpus_graph_tables.get("source_document_table_name"),"url":url}    
        )

                                        
        relations = await self.connection.query(
            """
                SELECT confidence,contexts,relationship,in.{additional_data,identifier,name},out.{additional_data,identifier,name} 
            FROM type::table($relation_table_name) WHERE source_document = type::thing($source_document_table_name,$url);""",
            params = {"relation_table_name":corpus_graph_tables.get("relation_table_name"),
                        "source_document_table_name":corpus_graph_tables.get("source_document_table_name"),"url":url}    
        )
        return {
            "source_document_info":source_document_info[0],
            "entities":entities,
            "relations":relations
        }
    

    async def corpus_graph_data(self,corpus_table_detail:dict,graph_start_date:str = None,graph_end_date:str = None,
                                    identifier:str = None,relationship:str = None,name_filter:str = None,url:str = None,graph_size_limit:int = 100):

        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")
        select_sql_string = """
                    SELECT 
                    confidence, 
                    relationship, 
                    source_document,
                    out.{id,entity_type,name,source_document,identifier},
                    in.{id,entity_type,name,source_document,identifier}
                    FROM type::table($relation_table_name)
            """ 
        
        params = {"relation_table_name":corpus_graph_tables.get("relation_table_name")} 
        
        graph_title = "Graph "
        where_clause = ""
        if graph_start_date:
            start_date = datetime.datetime.strptime(graph_start_date, '%Y-%m-%d')
            if where_clause:
                where_clause += " AND "
            where_clause += """ <datetime>(type::field($relation_date_field)) >= $start_date"""
            params["start_date"] = start_date
            params["entity_date_field"] = corpus_graph_tables.get("entity_date_field")
            params["relation_date_field"] = corpus_graph_tables.get("relation_date_field")
            graph_title += f"from {start_date.strftime('%Y-%m-%d')} "
        else:
            start_date = None

        if graph_end_date:
            end_date = datetime.datetime.strptime(graph_end_date, '%Y-%m-%d')
            if where_clause:
                where_clause += " AND "
            where_clause += """ <datetime>(type::field($relation_date_field)) <= $end_date"""
            params["end_date"] = end_date
            params["entity_date_field"] = corpus_graph_tables.get("entity_date_field")
            params["relation_date_field"] = corpus_graph_tables.get("relation_date_field")
            graph_title += f"to {end_date.strftime('%Y-%m-%d')} "
        else:
            end_date = None

        if identifier:
            if where_clause:
                where_clause += " AND "
            where_clause += """ (in.identifier = $identifier OR out.identifier = $identifier)"""
            params["identifier"] = identifier
            graph_title += f"for {identifier} "


        if name_filter:
            if where_clause:
                where_clause += " AND "
            where_clause += """ (in.name @1@ $name_filter or out.name  @2@ $name_filter)"""
            params["name_filter"] = name_filter
            graph_title += f""" "{name_filter}" """


        if relationship:    
            if where_clause:
                where_clause += " AND "
            where_clause += """ relationship = $relationship"""
            params["relationship"] = relationship
            graph_title += f"with relationship {relationship} "

        if url:   
            url = unformat_url_id(url)
            if where_clause:
                where_clause += " AND "
            where_clause += """ (source_document.url = $url 
                        OR in.source_document.url = $url 
                        OR out.source_documen.url = $url)"""
            params["url"] = url
            graph_title += f"for {url} "

        if where_clause:
            select_sql_string += " WHERE " + where_clause

        select_sql_string += f" LIMIT {graph_size_limit} FETCH in.source_document, out.source_document;"
        



        graph_data = await self.connection.query(
            select_sql_string ,
            params = params 
        )
        graph_size = len(graph_data)

        return {
            "graph_data": convert_corpus_graph_to_ux_data(graph_data),
            "graph_size": graph_size,
            "graph_title": graph_title,
            "graph_id": format_url_id(graph_title.replace(" ","_"))
        }
    
    async def source_document_detail(self,corpus_table_detail:dict,document_id):
        document = await self.connection.query(
            """RETURN fn::load_document_detail($corpus_table,$document_id)""",params = {"corpus_table":corpus_table_detail["table_name"],"document_id":document_id}    
        )
        return document[0]
        