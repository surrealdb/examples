"""Insert Edgar data into SurrealDB."""

import ast

import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag import loggers
import surrealdb_rag.constants as constants


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams, SurrealDML

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input EDGAR Graph data",db_params,model_params)



# Chunk size for batch processing
BATCH_SIZE = 100


def count_csv_rows_pandas_chunked(csv_filepath, chunk_size=1000): # Adjust chunk_size as needed
    """Counts CSV rows accurately using pandas chunking, handling embedded newlines."""
    total_rows = 0
    csv_chunk_iterator = pd.read_csv(csv_filepath, chunksize=chunk_size)
    for chunk_df in csv_chunk_iterator:
        total_rows += len(chunk_df) # Add the number of rows in each chunk
    return total_rows

MAX_RETRY_COUNT = 3
def insert_chunk_of_rows(insert_record_surql: str, batch_rows: list, retry_count = 0) -> None:
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
            


def insert_rows(entity_table_name, replation_table_name, input_file, total_chunks, using_glove, using_fasttext):
   # Iterate through chunks and insert records
    #schema of the csv

    file_keys = {
        "url":"",
        "filer_cik":"",
        "form":"",
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
    

    insert_entity_record_surql = SurrealDML.INSERT_GRAPH_ENTITY_RECORDS(entity_table_name)
    insert_relation_record_surql = SurrealDML.INSERT_GRAPH_RELATION_RECORDS(entity_table_name,replation_table_name)
    #with tqdm.tqdm(total=total_chunks, desc="Inserting Batches") as pbar: # Progress bar for batches
    with tqdm.tqdm(total=total_chunks,desc="Inserting Batches") as pbar: # Progress bar for batches
        row_counter = 0 # Track row number for batching
        batch_entity_rows = [] # List to accumulate rows for a batch
        batch_relation_rows = [] # List to accumulate rows for a batch
        with pd.read_csv(input_file, chunksize=BATCH_SIZE) as csv_chunk_iterator: # Iterate through CSV chunks
            for chunk_df in csv_chunk_iterator: # chunk_df is a DataFrame chunk

                for index, row in chunk_df.iterrows(): # Iterate over rows in the chunk DataFrame
                    row_counter += 1

                    if str(row["entity_type"]) == "relation": 
      
                        if row["entity_cik"]:
                            entity1 = [row["url"],"company",row["entity_cik"]]
                        else:
                            entity1 = [row["url"],"person",row["entity_name"]]
                        
                        if row["entity2_cik"]:
                            entity2 = [row["url"],"company",row["entity2_cik"]]
                        else:
                            entity2 = [row["url"],"person",row["entity2_name"]]


                        formatted_row = {
                            "entity1": entity1,
                            "entity2": entity2,
                            "source_document": row["url"],
                            "confidence": row["confidence"],
                            "relationship": row["relationship"],
                            "contexts": row["contexts"],
                            "content_glove_vector":ast.literal_eval(row["content_glove_vector"]) if using_glove else None,
                            "content_fasttext_vector":ast.literal_eval(row["content_fasttext_vector"]) if using_fasttext else None
                        }
                        batch_relation_rows.append(formatted_row) # Add formatted row to the batch
                    else:

                        formatted_row = {
                            "source_document": row["url"],
                            "entity_type": row["entity_type"],
                            "identifier": row["entity_cik"] if row["entity_type"]=="company" else row["entity_name"],
                            "name": row["entity_name"],
                            "contexts": row["contexts"],
                            "content_glove_vector":ast.literal_eval(row["content_glove_vector"]) if using_glove else None,
                            "content_fasttext_vector":ast.literal_eval(row["content_fasttext_vector"]) if using_fasttext else None,
                            "additional_data": {
                                    "form": row["form"],
                                    "filer_cik": row["filer_cik"],
                                    "form": row["form"],
                            }
                        }

                                
                        batch_entity_rows.append(formatted_row) # Add formatted row to the batch

                    if row_counter % BATCH_SIZE == 0: # Batch size reached, insert batch
                       insert_chunk_of_rows(insert_entity_record_surql, batch_entity_rows,insert_relation_record_surql,batch_relation_rows)
                       batch_entity_rows = [] # Clear batch after insert
                       batch_relation_rows = [] # Clear batch after insert
                       pbar.update(1) # Update progress bar after each batch

            # Insert any remaining rows in the last batch (if less than BATCH_SIZE)
            if batch_entity_rows or batch_relation_rows:
                insert_chunk_of_rows(insert_entity_record_surql, batch_entity_rows,insert_relation_record_surql,batch_relation_rows)
                batch_entity_rows = [] # Clear batch after insert
                batch_relation_rows = [] # Clear batch after insert
                pbar.update(1) # Update progress bar after each batch
               

        



"""Main entrypoint to insert embeddings into SurrealDB."""
def surreal_edgar_insert() -> None:

    input_file = constants.DEFAULT_EDGAR_GRAPH_PATH
    table_name = ""
    entity_display_name = ""
    relation_display_name = ""


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
    args_loader.AddArg("input_file","if","input_file","The path to the csv to insert. (default{0})",input_file)
    args_loader.AddArg("table_name","tn","entity_table_name","The sql corpuls table name the 2 will be created with suffixes _entity and _relation (eg embedded_edgar_10k_2025). (default{0})",table_name)
    args_loader.AddArg("entity_display_name","edn","entity_display_name","The name of the entity table (eg 10-K filings people and companies). (default{0})",display_name)
    args_loader.AddArg("relation_display_name","rdn","relation_display_name","The name of the enity table to see when selecting in the ux (eg '10k filings for 2025 people and companies'). (default{0})",display_name)
    
    # Parse command-line arguments
    args_loader.LoadArgs()


    if args_loader.AdditionalArgs["input_file"]["value"]:
        input_file = args_loader.AdditionalArgs["input_file"]["value"]
    
    if args_loader.AdditionalArgs["table_name"]["value"]:
        table_name = args_loader.AdditionalArgs["table_name"]["value"]
    else:
        raise Exception("You must specify a table name with the -tn flag")
    
    if args_loader.AdditionalArgs["entity_display_name"]["value"]:
        entity_display_name = args_loader.AdditionalArgs["entity_display_name"]["value"]
    else:
        raise Exception("You must specify a display name with the -edn flag")

    if args_loader.AdditionalArgs["relation_display_name"]["value"]:
        relation_display_name = args_loader.AdditionalArgs["relation_display_name"]["value"]
    else:
        raise Exception("You must specify a display name with the -rdn flag")


    logger = loggers.setup_logger("SurrealEDGARGraphInsert")

    logger.info(args_loader.string_to_print())

    # Retrieve embedding models from arguments
    embed_models_str = args_loader.AdditionalArgs["embed_models"]["value"]
    embed_models = embed_models_str.split(",")
    
    # Validate embedding models
    if len(embed_models)<1:
        raise Exception("You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")
    fs_version = args_loader.AdditionalArgs["fast_text_version"]["value"]
    

    using_fasttext = False
    using_glove = False
    for embed_model in embed_models:
        if embed_model=="FASTTEXT":
            using_fasttext = True
            if not fs_version:
                raise Exception("You must specify at a FASTTEXT version with the -fsv flag")
        if embed_model=="GLOVE":
            using_glove = True
        if embed_model not in SurrealDML.EMBED_MODEL_DEFINITIONS:
              raise Exception(f"{embed_model} is invalid, You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")
    


    # Create embedding model mappings
    embed_model_mappings = []
    for embed_model in embed_models:
        if embed_model in SurrealDML.EMBED_MODEL_DEFINITIONS:
            field_name = SurrealDML.EMBED_MODEL_DEFINITIONS[embed_model]["field_name"]
            model_definition = SurrealDML.EMBED_MODEL_DEFINITIONS[embed_model]["model_definition"]
            # if custom fast text insert the version
            if embed_model == "FASTTEXT":
                model_definition[1] = fs_version
            embed_model_mappings.append({"model_id": model_definition, "field_name": field_name})



    logger.info(f"Calculating rows in file {input_file}")
    # num_rows_csv = sum(1 for row in open(input_file, 'r', encoding='utf-8')) - 1 # Subtract header row 
    num_rows_csv = count_csv_rows_pandas_chunked(input_file)
    total_rows = num_rows_csv # Use this count for batching and progress bar
    total_chunks = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE

    logger.info(f"Total rows in CSV: {total_rows}") # Debugging - check row count
    
    logger.info(f"Executting DDL for {table_name}")

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info(f"Connecting to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")

        # Read and execute table DDL that creates the tables and indexes if missing
        with open(constants.CORPUS_GRAPH_TABLE_DDL) as f: 
            surlql_to_execute = f.read()
            surlql_to_execute = surlql_to_execute.format(corpus_table = table_name)
            
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))


        # Update corpus table information
        logger.info(f"Deleting any existing corpus table info for {table_name}")
        SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.DELETE_CORPUS_GRAPH_TABLE_INFO(table_name),params={"embed_models":embed_model_mappings}))
    
    logger.info("Inserting rows into SurrealDB")

    entity_table_name = f"{table_name}_entity"
    relation_table_name = f"{table_name}_relation"


    insert_rows(entity_table_name,relation_table_name, input_file, total_chunks, using_glove, using_fasttext)


    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info(f"Connecting to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")

        # Update corpus table information
        logger.info(f"Updating corpus table info for {table_name}")
        SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.UPDATE_CORPUS_GRAPH_TABLE_INFO(table_name),params={
            "entity_display_name": entity_display_name,
            "entity_table_name": entity_table_name,
            "relation_display_name": relation_display_name, 
            "relation_table_name": relation_table_name
            }))





if __name__ == "__main__":
    surreal_edgar_insert()