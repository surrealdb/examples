"""Insert Edgar data into SurrealDB."""

import ast

import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag.helpers import loggers
import surrealdb_rag.helpers.constants as constants
import datetime
from surrealdb_rag.helpers.llm_handler import RAGChatHandler,ModelListHandler

from surrealdb_rag.data_processing.edgar_graph_extractor import get_public_companies


from surrealdb_rag.helpers.constants import ArgsLoader
from surrealdb_rag.helpers.params import DatabaseParams, ModelParams, SurrealParams
from surrealdb_rag.helpers.surreal_dml import SurrealDML

from surrealdb_rag.helpers.corpus_data_handler import CorpusTableListHandler

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input EDGAR Graph data",db_params,model_params)



# Chunk size for batch processing
CHUNK_SIZE = 100

MAX_RETRY_COUNT = 3


def insert_chunk_of_rows(insert_record_surql: str, batch_rows: list, retry_count = 0) -> None:

    """
    Inserts a batch of rows into SurrealDB, with retry logic for handling transient errors.

    This function attempts to insert a chunk of data into the database. If an exception occurs,
    it retries the insertion up to a maximum number of times.

    Args:
        insert_record_surql (str): The SurrealQL query for inserting records.
        batch_rows (list): A list of dictionaries representing the rows to insert.
        retry_count (int, optional): The current retry count. Defaults to 0.

    Raises:
        Exception: If the insertion fails after multiple retries.
    """


    try:
        with Surreal(db_params.DB_PARAMS.url) as connection:
            connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
            connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
            SurrealParams.ParseResponseForErrors(connection.query_raw(
                insert_record_surql, params={"records": batch_rows}
            ))
    except Exception as e:
        if retry_count >= MAX_RETRY_COUNT:
            raise Exception(f"Failed to insert chunk of rows after multiple retries {e}")
        else:
            insert_chunk_of_rows(insert_record_surql, batch_rows, retry_count + 1)
            


def insert_rows(entity_table_name,relation_table_name,source_document_table_name,graph_data_df, company_metadata_lookup, using_glove, using_fasttext,incrimental_load):
    """
    Inserts data from a DataFrame into SurrealDB tables (entities, relations, source documents).

    This function processes the DataFrame in chunks, formatting the data and inserting it into the
    appropriate SurrealDB tables. It handles different entity types (person, company, relation)
    and incorporates metadata and embeddings.

    Args:
        entity_table_name (str): The name of the entity table in SurrealDB.
        relation_table_name (str): The name of the relation table in SurrealDB.
        source_document_table_name (str): The name of the source document table in SurrealDB.
        graph_data_df (pd.DataFrame): The DataFrame containing the graph data to insert.
        company_metadata_lookup (dict): A dictionary for detailed company metadata (key: CIK, value: company metadata dict).
        using_glove (bool): Flag indicating whether GloVe embeddings are used.
        using_fasttext (bool): Flag indicating whether FastText embeddings are used.
        incremental_load (bool): Flag indicating whether to perform an incremental load.
    """
    file_keys = {
        "url":"",
        "filer_cik":"",
        "form":"",
        "filing_date":"",
        "filer_company_name":"",
        "accession_no":"",
        "entity_type":"",
        "entity_name":"",
        "entity_cik":"",
        "entity2_name":"",
        "entity2_cik":"",
        "relationship":"",
        "confidence":0,
        "contexts":[],
        "glove_vector":[],
        "fasttext_vector":[]
        }.keys()

    insert_source_documents_surql = SurrealDML.UPSERT_SOURCE_DOCUMENTS(source_document_table_name)

    # insert_entity_record_surql = SurrealDML.UPSERT_GRAPH_ENTITY_RECORDS(entity_table_name,source_document_table_name)
    # insert_relation_record_surql = SurrealDML.UPSERT_GRAPH_RELATION_RECORDS(entity_table_name,relation_table_name,source_document_table_name)

    if incrimental_load:
        insert_entity_record_surql = SurrealDML.UPSERT_GRAPH_ENTITY_RECORDS(entity_table_name,source_document_table_name)
        insert_relation_record_surql = SurrealDML.UPSERT_GRAPH_RELATION_RECORDS(entity_table_name,relation_table_name,source_document_table_name)
    else:
        insert_entity_record_surql = SurrealDML.INSERT_GRAPH_ENTITY_RECORDS(entity_table_name,source_document_table_name)
        insert_relation_record_surql = SurrealDML.INSERT_GRAPH_RELATION_RECORDS(entity_table_name,relation_table_name,source_document_table_name)


    total_rows=len(graph_data_df)
    total_chunks = total_rows // CHUNK_SIZE + (
        1 if total_rows % CHUNK_SIZE else 0
    )   

    with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:
        for i in range(0, total_rows, CHUNK_SIZE):
            chunk_df = graph_data_df.iloc[i:i + CHUNK_SIZE]
            batch_entity_rows = [] 
            batch_relation_rows = []
            batch_source_document_rows = {}
            for index, row in chunk_df.iterrows(): # Iterate over rows in the chunk DataFrame

                source_document_row = {}
                source_document_row["url"] = row["url"]
                source_document_row["title"] = row["filer_company_name"] + ' ' + row["form"] + ' ' + row["filing_date"]
                source_document_row["additional_data"] = {
                                    "form": row["form"],
                                    "filer_cik": row["filer_cik"],
                                    "filing_date": row["filing_date"],
                                    "filer_company_name": row["filer_company_name"],
                                    "accession_no": row["accession_no"]
                                }
                batch_source_document_rows[row["url"]] = source_document_row

                
                formatted_row = {
                    "url": row["url"],
                    "contexts": ast.literal_eval(row["contexts"]),
                    "content_glove_vector":ast.literal_eval(row["glove_vector"]) if using_glove else None,
                    "content_fasttext_vector":ast.literal_eval(row["fasttext_vector"]) if using_fasttext else None,
                    "additional_data" : {
                                    "form": row["form"],
                                    "filer_cik": row["filer_cik"],
                                    "filing_date": row["filing_date"],
                                    "filer_company_name": row["filer_company_name"],
                                    "accession_no": row["accession_no"]
                                }
                }
                
                match row["entity_type"]:
                    case "relation":
                        try:
                            # company will have int in the cik field
                            entity1 = [row["url"],"company",str(int(row["entity_cik"]))]
                        except:
                            entity1 = [row["url"],"person",row["entity_name"]]
                        try:
                            # company will have int in the cik field
                            entity2 = [row["url"],"company",str(int(row["entity2_cik"]))]
                        except:
                            entity2 = [row["url"],"person",row["entity2_name"]]

                        formatted_row["entity1"] = entity1
                        formatted_row["entity2"] = entity2
                        formatted_row["confidence"] = row["confidence"]
                        try:
                            relationship = str(row["relationship"])
                        except:
                            relationship = "?"
                        formatted_row["relationship"] =  relationship
                        batch_relation_rows.append(formatted_row) # Add formatted row to the batch

                    case "person" | "company":
                        
                        identifier = str(int(row["entity_cik"])) if row["entity_type"]=="company" else row["entity_name"]
                        formatted_row["full_id"] = [row["url"],row["entity_type"],identifier]

                        formatted_row["entity_type"] = row["entity_type"]
                        formatted_row["identifier"] = identifier
                        formatted_row["name"] = row["entity_name"]
                        
                        if row["entity_type"] == "company":
                            try:
                                company_metadata = company_metadata_lookup[int(row["entity_cik"])]
                                formatted_row["additional_data"]["company_metadata"] = company_metadata
                            except:
                                a = ""

                        batch_entity_rows.append(formatted_row) # Add formatted row to the batch
                    case _:
                        a = ""
                
            pbar.set_description("Ins. docs")
            insert_chunk_of_rows(insert_source_documents_surql, list(batch_source_document_rows.values()))
            pbar.set_description("Ins. ents")
            insert_chunk_of_rows(insert_entity_record_surql, batch_entity_rows)
            pbar.set_description("Ins. rels")
            insert_chunk_of_rows(insert_relation_record_surql,batch_relation_rows)
            pbar.update(1) # Update progress bar after each batch
            



        


def surreal_edgar_graph_insert() -> None:
    """
    Main function to insert EDGAR graph data into SurrealDB.

    This function reads graph data from a CSV file, configures the SurrealDB connection,
    and calls the `insert_rows` function to perform the data insertion. It also handles
    command-line arguments for customization.
    """
    input_file = constants.DEFAULT_EDGAR_GRAPH_PATH
    table_name = ""
    start_date_str = ""
    end_date_str = ""
    incrimental_load = True


    # Add command-line argument for embedding models
    args_loader.AddArg(
        "embed_models",
        "ems",
        "embed_models",
        "The Embed models you'd like to calculate sepearated by , can be GLOVE,FASTTEXT eg -ems FASTTEXT,GLOVE will calculate both FASTTEXT and GLOVE. (default{0})",
        "GLOVE,FASTTEXT"
    )
    args_loader.AddArg( 
        "fast_text_version",
        "fsv",
        "fast_text_version",
        "The name of the FASTTEXT version you uploaded. (default{0})",
        ""
    )

    args_loader.AddArg("start_date","edsd","start_date","Start filing date in format '%Y-%m-%d' for filtering. (default{0} blank string doesn't filter)",start_date_str)
    args_loader.AddArg("end_date","eded","end_date","End filing date in format '%Y-%m-%d' for filtering. (default{0} blank string doesn't filter)",end_date_str)
    args_loader.AddArg("input_file","if","input_file","The path to the csv to insert. (default{0})",input_file)
    args_loader.AddArg("table_name","tn","entity_table_name","The sql corpuls table name the 2 will be created with suffixes _entity and _relation (eg embedded_edgar_10k_2025). (default{0})",table_name)
    args_loader.AddArg("incrimental_load","il","incrimental_load","do an incremental load? or overwrite entire database?. (default{0})",incrimental_load)

    # Parse command-line arguments
    args_loader.LoadArgs()


    if args_loader.AdditionalArgs["input_file"]["value"]:
        input_file = args_loader.AdditionalArgs["input_file"]["value"]
    
    if args_loader.AdditionalArgs["table_name"]["value"]:
        table_name = args_loader.AdditionalArgs["table_name"]["value"]
    else:
        raise Exception("You must specify a table name with the -tn flag")
    
    if args_loader.AdditionalArgs["incrimental_load"]["value"]:
        incrimental_load = str(args_loader.AdditionalArgs["incrimental_load"]["value"]).lower()in ("true","yes","1")


    logger = loggers.setup_logger("SurrealEDGARGraphInsert")
    logger.info(args_loader.string_to_print())

    graph_data_df = pd.read_csv(input_file)

    graph_data_df['filing_datetime'] = pd.to_datetime(graph_data_df['filing_date'], errors='coerce')

    if args_loader.AdditionalArgs["start_date"]["value"]:
        start_date = datetime.datetime.strptime(args_loader.AdditionalArgs["start_date"]["value"], '%Y-%m-%d')
        graph_data_df = graph_data_df[graph_data_df["filing_datetime"] >= start_date]
    
    if args_loader.AdditionalArgs["end_date"]["value"]:
        end_date = datetime.datetime.strptime(args_loader.AdditionalArgs["end_date"]["value"], '%Y-%m-%d')
        graph_data_df = graph_data_df[graph_data_df["filing_datetime"] >= end_date]


    total_rows = len(graph_data_df)

    logger.info(f"Total rows in CSV: {total_rows}") # Debugging - check row count
    logger.info(f"Executting DDL for {table_name}")

    logger.info("Getting public companies metadata")


    using_fasttext = False
    using_glove = False

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info(f"Connecting to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")
        


        corpus_list = CorpusTableListHandler(connection,model_params)

        
        corpus_tables = corpus_list.available_corpus_tables_sync()
        embed_models = corpus_tables[table_name]["embed_models"]
        for embed_model in embed_models:
            if embed_model["model_trainer"] == "GLOVE":
                using_glove = True
            if embed_model["model_trainer"] == "FASTTEXT":
                using_fasttext = True

        if not (using_glove or using_fasttext):
            raise Exception("You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI for the core corpus table. Check your corpus table definition")
    

        if not incrimental_load:
            # Read and execute table DDL that creates the tables and indexes if missing
            logger.info(f"Executting DDL for {table_name}")
            with open(constants.CORPUS_GRAPH_TABLE_DDL) as f: 
                surlql_to_execute = f.read()
                surlql_to_execute = surlql_to_execute.format(corpus_table = table_name)
                
                SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))


            # Update corpus table information
            logger.info(f"Deleting any existing corpus table info for {table_name}")
            SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.DELETE_CORPUS_GRAPH_TABLE_INFO(table_name)))
    
    logger.info("Inserting rows into SurrealDB")

    entity_table_name = f"{table_name}_entity"
    relation_table_name = f"{table_name}_relation"
    source_document_table_name = f"{table_name}_source_document"


    insert_rows(entity_table_name,relation_table_name,source_document_table_name, graph_data_df, company_metadata_lookup, using_glove, using_fasttext,incrimental_load)

    if not incrimental_load:
        with Surreal(db_params.DB_PARAMS.url) as connection:
            logger.info(f"Connecting to SurrealDB")
            connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
            connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
            logger.info("Connected to SurrealDB")

            # Update corpus table information
            logger.info(f"Updating corpus table info for {table_name}")
            SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.UPDATE_CORPUS_GRAPH_TABLE_INFO(table_name),params={
                "entity_table_name": entity_table_name,
                "relation_table_name": relation_table_name,
                "source_document_table_name": source_document_table_name,
                "entity_date_field": "additional_data.filing_date",
                "relation_date_field": "additional_data.filing_date"
                }))





if __name__ == "__main__":
    surreal_edgar_graph_insert()