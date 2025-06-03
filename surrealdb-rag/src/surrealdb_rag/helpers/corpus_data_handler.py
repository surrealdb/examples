

from surrealdb_rag.helpers.params import DatabaseParams, ModelParams, SurrealParams
from surrealdb import AsyncSurreal, Surreal
from typing import Union
import datetime
from surrealdb_rag.helpers.ux_helpers import *

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
SurrealQL query to select corpus table information.

This query retrieves information about corpus tables, including display names, table names,
embedding models, additional data keys, and related graph tables. It also fetches the
date range for the relation table.
"""

class CorpusTableListHandler():
    """
    Provides methods for retrieving available corpus tables and their metadata.

    This class interacts with the SurrealDB database to fetch information about available
    corpus tables, including details about embedded models and associated graph tables.
    """
   
    def __init__(self, connection:Union[AsyncSurreal, Surreal],model_params:ModelParams):
        """
        Initializes the CorpusTableListHandler.

        Args:
            connection (AsyncSurreal): Asynchronous SurrealDB connection.
            model_params (ModelParams): Model parameters.
        """
        self.CORPUS_TABLES = {}
        self.connection = connection
        self.model_params = model_params
        
        
    
    

    def populate_corpus_tables(self,corpus_tables):

        """
        Populates the internal dictionary with corpus table information.

        This method processes the raw data retrieved from the database, filtering out
        OpenAI models based on the availability of the OpenAI API key and formatting
        the data for easier access.

        Args:
            corpus_tables (list): A list of dictionaries, where each dictionary represents a corpus table.

        Returns:
            dict: A dictionary where keys are table names and values are dictionaries containing table metadata.
        """


        # Filter out OpenAI models if API key is absent
        for corpus_table in corpus_tables:
            
            # create an dict item for table_name
            table_name = corpus_table["table_name"]
            self.CORPUS_TABLES[table_name] = {}
            self.CORPUS_TABLES[table_name]["display_name"] = corpus_table["display_name"]
            self.CORPUS_TABLES[table_name]["table_name"] = corpus_table["table_name"]
            self.CORPUS_TABLES[table_name]["additional_data_keys"] = corpus_table["additional_data_keys"]
            self.CORPUS_TABLES[table_name]["embed_models"] = []
            #datetime not serializable
            if corpus_table["corpus_graph_tables"] and corpus_table["corpus_graph_tables"]["date_range"]:
                self.CORPUS_TABLES[table_name]["corpus_graph_tables"] = corpus_table["corpus_graph_tables"]
                self.CORPUS_TABLES[table_name]["corpus_graph_tables"]["date_range"]["min"] = str(corpus_table["corpus_graph_tables"]["date_range"]["min"])
                self.CORPUS_TABLES[table_name]["corpus_graph_tables"]["date_range"]["max"] = str(corpus_table["corpus_graph_tables"]["date_range"]["max"])
            else:
                self.CORPUS_TABLES[table_name]["corpus_graph_tables"] = None

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


    
    async def available_corpus_tables(self):

        """
        Asynchronously retrieves a dictionary of available corpus tables.

        This method fetches corpus table information from the database and populates the
        internal dictionary. If the data is already cached, it returns the cached data.

        Returns:
            dict: A dictionary where keys are table names and values are dictionaries containing table metadata.
        """
         

        if self.CORPUS_TABLES != {}:
            return self.CORPUS_TABLES 
        else:
            self.CORPUS_TABLES = {}
            corpus_tables = await self.connection.query(CORPUS_TABLE_SELECT)
            return self.populate_corpus_tables(corpus_tables)


            
    def available_corpus_tables_sync(self):
        """
        Synchronously retrieves a dictionary of available corpus tables.

        This method is a synchronous version of `available_corpus_tables`, suitable for
        use in contexts where asynchronous operations are not supported.

        Returns:
            dict: A dictionary where keys are table names and values are dictionaries containing table metadata.
        """
        if self.CORPUS_TABLES != {}:
            return self.CORPUS_TABLES 
        else:
            self.CORPUS_TABLES = {}
            corpus_tables = self.connection.query(CORPUS_TABLE_SELECT)
            return self.populate_corpus_tables(corpus_tables)



        
class CorpusDataHandler():

    """
    Provides methods for querying data within a specific corpus.

    This class handles interactions with the SurrealDB database to retrieve information
    about entities, relationships, and source documents within a given corpus.
    It also includes methods for LLM integration.
    """

    GEMINI_CHAT_COMPLETE = """RETURN fn::gemini_chat_complete($llm,$prompt_with_context,$input,$google_token);"""
    """
    SurrealQL query to complete a chat using the Gemini LLM.
    """

    OPENAI_CHAT_COMPLETE = """RETURN fn::openai_chat_complete($llm,$prompt_with_context, $input, $temperature, $openai_token);"""
    """
    SurrealQL query to complete a chat using the OpenAI LLM.
    """

    def __init__(self,connection:AsyncSurreal,corpus_table_info:dict):
        """
        Initializes the CorpusDataHandler.

        Args:
            connection (AsyncSurreal): Asynchronous SurrealDB connection.
            corpus_table_info (dict): Metadata about the corpus table being handled.
        """
        self.connection = connection
        self.corpus_table_info = corpus_table_info

    async def query_additional_data(self,additional_data_field:str):
        """
        Queries additional data for the corpus table.

        Args:
            additional_data_field (str): The field name to query within the additional_data.

        Returns:
            list: A list of results from the query.
        """
        return await self.connection.query(
                """RETURN fn::select_additional_data($corpus_table,$key)""",vars = {"corpus_table":self.corpus_table_info["table_name"],"key":additional_data_field}    
            )
    


    async def relation_detail(self,corpus_table_detail:dict,identifier_in:str,identifier_out:str,relationship:str):

        """
        Retrieves details about a specific relationship between two entities.

        Args:
            corpus_table_detail (dict): Metadata about the corpus table.
            identifier_in (str): Identifier of the source entity.
            identifier_out (str): Identifier of the target entity.
            relationship (str): The type of relationship.

        Returns:
            list: A list of results from the query, containing information about the relationship.
        """

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
                vars = {"relation_table_name":corpus_graph_tables.get("relation_table_name"),"identifier_in":identifier_in,"identifier_out":identifier_out,"relationship":relationship} 
            )
        return relation_info



    async def entity_detail(self,corpus_table_detail:dict,identifier:str):

        """
        Retrieves details about a specific entity and its relations.

        Args:
            corpus_table_detail (dict): Metadata about the corpus table.
            identifier (str): The identifier of the entity.

        Returns:
            dict: A dictionary containing information about the entity, its relations, and mentions.
        """


        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")
        
        entity_relations = await self.connection.query(
            """
                RETURN array::group(
                SELECT VALUE <->?.{confidence,contexts,relationship,source_document.{url,title},
                    in.{entity_type, identifier, name},
                    out.{entity_type, identifier, name}} 
                FROM type::table($entity_table_name) WHERE identifier=$identifier);
                    """,
            vars = {"entity_table_name":corpus_graph_tables.get("entity_table_name"),"identifier":identifier} 
        )

        entity_relations_dict = organize_relations_for_ux(entity_relations,identifier)

        entity_mentions = await self.connection.query("""
            RETURN array::group (
                SELECT VALUE {"source_document":source_document,"contexts":contexts,"additional_data":additional_data}
                    FROM  type::table($entity_table_name) WHERE identifier = $identifier FETCH source_document
                )
            ;""",
            vars = {"entity_table_name":corpus_graph_tables.get("entity_table_name"),"identifier":identifier} 
        )

        entity_info = await self.connection.query("""
            SELECT name,identifier,entity_type FROM type::table($entity_table_name) WHERE identifier = $identifier LIMIT 1
            ;""",
            vars = {"entity_table_name":corpus_graph_tables.get("entity_table_name"),"identifier":identifier} 
        )
        
        return {
            "entity_relations":list(entity_relations_dict.values()),
            "entity_mentions":entity_mentions,
            "entity_info":entity_info[0]
        }
    


    async def source_document_details(self,corpus_table_detail:dict,url:str):

        """
        Retrieves details about a specific source document and its associated entities and relations.

        Args:
            corpus_table_detail (dict): Metadata about the corpus table.
            url (str): The URL or identifier of the source document.

        Returns:
            dict: A dictionary containing information about the source document, its entities, and relations.
        """


        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")

        url = unformat_url_id(url)

        source_document_info = await self.connection.query(
            """SELECT additional_data,title,url FROM type::thing($source_document_table_name,$url);""",
            vars = {"source_document_table_name":corpus_graph_tables.get("source_document_table_name"),"url":url}    
        )
        entities = await self.connection.query(
            f"""SELECT * FROM {corpus_graph_tables.get("entity_table_name")}:[$url,None,None]..[$url,..,..];""",
            vars = {"source_document_table_name":corpus_graph_tables.get("source_document_table_name"),"url":url}    
        )

                                        
        relations = await self.connection.query(
            """
                SELECT confidence,contexts,relationship,in.{additional_data,identifier,name},out.{additional_data,identifier,name} 
            FROM type::table($relation_table_name) WHERE source_document = type::thing($source_document_table_name,$url);""",
            vars = {"relation_table_name":corpus_graph_tables.get("relation_table_name"),
                        "source_document_table_name":corpus_graph_tables.get("source_document_table_name"),"url":url}    
        )
        return {
            "source_document_info":source_document_info[0],
            "entities":entities,
            "relations":relations
        }
    

    async def corpus_graph_data(self,corpus_table_detail:dict,graph_start_date:str = None,
                                graph_end_date:str = None,
                                    identifier:str = None,relationship:str = None,
                                    name_filter:str = None,url:str = None,
                                    context_filter:str = None,
                                    embed_model:any = None,
                                    graph_size_limit:int = 100):


        """
        Retrieves graph data for a corpus, with filtering options.

        Args:
            corpus_table_detail (dict): Metadata about the corpus table.
            graph_start_date (str, optional): Start date for filtering relationships. Defaults to None.
            graph_end_date (str, optional): End date for filtering relationships. Defaults to None.
            identifier (str, optional): Identifier of an entity to filter relations. Defaults to None.
            relationship (str, optional): Type of relationship to filter. Defaults to None.
            name_filter (str, optional): Filter entities by name. Defaults to None.
            url (str, optional): Filter by source document URL. Defaults to None.
            context_filter (str, optional): Filter vector search on the relation contexts, will ignore other parameters if using. Defaults to None.
            embed_model (str, optional): Required if using context_filter. Defaults to None.
            graph_size_limit (int, optional): Maximum number of relationships to return. Defaults to 100.

        Returns:
            dict: A dictionary containing graph data and metadata.
        """


        corpus_graph_tables = corpus_table_detail.get("corpus_graph_tables")
        select_sql_string = """
                    SELECT 
                    confidence, 
                    relationship, 
                    source_document,
                    out.{id,entity_type,name,source_document,identifier},
                    in.{id,entity_type,name,source_document,identifier}
            """ 
        
        params = {"relation_table_name":corpus_graph_tables.get("relation_table_name")} 
        
        graph_title = "Graph "
        where_clause = ""



        vector_fetch_sql = ""

        #context filter isn't working in combo right now.
        if context_filter:
            if where_clause:
                where_clause += " AND "

                           

            vector_fetch_sql = """
                    LET $threshold = 0.7;
                    LET $embedding_model = type::thing('embedding_model_definition',$embedding_model_id);
                    LET $vector = IF $embedding_model.model_trainer == "OPENAI" THEN 
                        fn::openai_embeddings_complete($embedding_model.version, $context_filter, $openai_token)
                    ELSE
                        fn::sentence_to_vector($context_filter,$embedding_model)
                    END;
                    """
            

            params["context_filter"] = context_filter
            params["embedding_model_id"] = embed_model["model"]
            params["corpus_table"] =  corpus_table_detail.get("table_name")
            match embed_model["model_trainer"]:
                case "GLOVE":
                    context_vector_field = "context_glove_vector"
                case "FASTTEXT":
                    context_vector_field = "context_fasttext_vector"
                case "OPENAI":
                    context_vector_field = "context_openai_vector"
                case _:
                    raise Exception(f"Unknown model_trainer {embed_model['model_trainer']}")
                
            # Add the similarity score to the select statement
            select_sql_string += f", vector::similarity::cosine({context_vector_field}, $vector) AS similarity_score "

            where_clause += f"""
                {context_vector_field} <|{graph_size_limit},{graph_size_limit}|> $vector
                     """
            




            

            graph_title += f" '{context_filter}'"


        #context filter isn't working in combo right now.
        else:
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



        # Add the from statment
        select_sql_string += " FROM type::table($relation_table_name) "

        if where_clause:
            select_sql_string += " WHERE " + where_clause
            

        if vector_fetch_sql:
            sql_to_execute = f"""
                {vector_fetch_sql}
                SELECT * FROM (
                    {select_sql_string}
                    FETCH in.source_document, out.source_document
                )
                WHERE similarity_score >= $threshold;
            """


            graph_data = SurrealParams.ParseResponseForErrors( await self.connection.query_raw(
                sql_to_execute ,
                params = params 
                )
            )
            #there are 2 let statements before the query
            graph_data = graph_data["result"][3]["result"]
        else:

            sql_to_execute = f"""
                {select_sql_string}
                LIMIT {graph_size_limit} FETCH in.source_document, out.source_document;
            """

            graph_data = await self.connection.query(
                sql_to_execute ,
                vars = params 
            )
        graph_size = len(graph_data)

        return {
            "graph_data": convert_corpus_graph_to_ux_data(graph_data),
            "graph_size": graph_size,
            "graph_title": graph_title,
            "graph_id": format_url_id(graph_title.replace(" ","_"))
        }
    
    async def source_document_detail(self,corpus_table_detail:dict,document_id):

        """
        Retrieves detailed information about a specific source document.

        Args:
            corpus_table_detail (dict): Metadata about the corpus table.
            document_id: The ID of the source document.

        Returns:
            dict: A dictionary containing details about the source document.
        """
         
        document = await self.connection.query(
            """RETURN fn::load_document_detail($corpus_table,$document_id)""",vars = {"corpus_table":corpus_table_detail["table_name"],"document_id":document_id}    
        )
        return document[0]
        