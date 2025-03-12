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
args_loader = ArgsLoader("Input EDGAR data",db_params,model_params)

# Define table name and display name
TABLE_NAME = "embedded_edgar"
DISPLAY_NAME = "SEC 10k Filings"


# Chunk size for batch processing
CHUNK_SIZE = 100


def count_csv_rows_pandas_chunked(csv_filepath, chunk_size=1000): # Adjust chunk_size as needed
    """Counts CSV rows accurately using pandas chunking, handling embedded newlines."""
    total_rows = 0
    csv_chunk_iterator = pd.read_csv(csv_filepath, chunksize=chunk_size)
    for chunk_df in csv_chunk_iterator:
        total_rows += len(chunk_df) # Add the number of rows in each chunk
    return total_rows



"""Main entrypoint to insert embeddings into SurrealDB."""
def surreal_edgar_insert() -> None:
    # Add command-line argument for embedding models
    args_loader.AddArg(
        "embed_models",
        "ems",
        "embed_models",
        "The Embed models you'd like to calculate sepearated by , can be GLOVE,FASTTEXT eg -ems FASTTEXT,GLOVE will calculate both FASTTEXT and GLOVE. (default{})",
        "GLOVE,FASTTEXT"
    )
    args_loader.AddArg( 
        "fast_text_version",
        "fsv",
        "fast_text_version",
        "The name of the FASTTEXT version you uploaded. (default{})",
        ""
    )

    # Parse command-line arguments
    args_loader.LoadArgs()

    logger = loggers.setup_logger("SurrealEDGARInsert")

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



  

    # Read  records from CSV
    # too slow too much memory
    # edgar_records_df = pd.read_csv(constants.EDGAR_PATH,usecols=usecols)
    
    # # Calculate total rows and chunks
    # total_rows = len(edgar_records_df)
    # total_chunks = total_rows // CHUNK_SIZE + (
    #     1 if total_rows % CHUNK_SIZE else 0
    # )   
    # print(edgar_records_df.head())
    # print(edgar_records_df.describe())


    logger.info(f"Calculating rows in file {constants.EDGAR_PATH}")
    # num_rows_csv = sum(1 for row in open(constants.EDGAR_PATH, 'r', encoding='utf-8')) - 1 # Subtract header row 
    num_rows_csv = count_csv_rows_pandas_chunked(constants.EDGAR_PATH)
    total_rows = num_rows_csv # Use this count for batching and progress bar
    total_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE

    logger.info(f"Total rows in CSV: {total_rows}") # Debugging - check row count
    

    with Surreal(db_params.DB_PARAMS.url) as connection:

        logger.info(f"Connecting to SurrealDB")
        
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")

    
        
        logger.info(f"Executting DDL for {TABLE_NAME}")

        # Read and execute table DDL that creates the tables and indexes if missing
        with open(constants.CORPUS_TABLE_DDL) as f: 
            surlql_to_execute = f.read()
            surlql_to_execute = surlql_to_execute.format(corpus_table = TABLE_NAME)
            
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))


        # Update corpus table information
        logger.info(f"Deleting any existing corpus table info for {TABLE_NAME}")
        SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.DELETE_CORPUS_TABLE_INFO(TABLE_NAME),params={"embed_models":embed_model_mappings}))


        logger.info("Inserting rows into SurrealDB")
        # Iterate through chunks and insert records


        #schema of the csv
        file_keys = {
            "url":"",
            "company_name":"",
            "cik":"",
            "form":"",
            "accession_no":"",
            "company.ticker_display":"",
            "company.description":"",
            "company.category":"",
            "company.industry":"",
            "company.website":"",
            "filing_date":"",
            "file_path":"",
            "chunk":"",
            "content":"",
            "content_glove_vector":"",
            "content_fasttext_vector":"",
            }.keys()

        insert_record_surql = SurrealDML.INSERT_RECORDS(TABLE_NAME)
        #with tqdm.tqdm(total=total_chunks, desc="Inserting Batches") as pbar: # Progress bar for batches
        with tqdm.tqdm(total=total_chunks,desc="Inserting Batches") as pbar: # Progress bar for batches
            row_counter = 0 # Track row number for batching
            batch_rows = [] # List to accumulate rows for a batch
            with pd.read_csv(constants.EDGAR_PATH, chunksize=CHUNK_SIZE) as csv_chunk_iterator: # Iterate through CSV chunks
                for chunk_df in csv_chunk_iterator: # chunk_df is a DataFrame chunk
                    for index, row in chunk_df.iterrows(): # Iterate over rows in the chunk DataFrame
                        row_counter += 1

                        formatted_row ={
                            "url":str(row["url"]),
                            "title": f"{row['company.ticker_display']} {row['form']} {row['filing_date']}",
                            "text": str(row["content"]),
                            "content_glove_vector":ast.literal_eval(row["content_glove_vector"]) if using_glove else None,
                            "content_fasttext_vector":ast.literal_eval(row["content_fasttext_vector"]) if using_fasttext else None,
                            "additional_data": {
                                    "company_name": row["company_name"],
                                    "cik": row["cik"],
                                    "form": row["form"],
                                    "accession_no": row["accession_no"],
                                    "company_ticker_display": row["company.ticker_display"],
                                    "company_description": row["company.description"],
                                    "company_category": row["company.category"],
                                    "company_industry": row["company.industry"],
                                    "company_website": row["company.website"],
                                    "filing_date": row["filing_date"],
                            }
                        }
 
                               
                        batch_rows.append(formatted_row) # Add formatted row to the batch

                        if row_counter % CHUNK_SIZE == 0: # Batch size reached, insert batch
                            SurrealParams.ParseResponseForErrors(connection.query_raw(
                                insert_record_surql, params={"records": batch_rows}
                            ))
                            batch_rows = [] # Clear batch after insert
                            pbar.update(1) # Update progress bar after each batch

                # Insert any remaining rows in the last batch (if less than CHUNK_SIZE)
                if batch_rows:
                    SurrealParams.ParseResponseForErrors(connection.query_raw(
                        insert_record_surql, params={"records": batch_rows}
                    ))
                    pbar.update(1) # Update progress bar for the final batch


        


        # Update corpus table information
        logger.info(f"Updating corpus table info for {TABLE_NAME}")
        SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.UPDATE_CORPUS_TABLE_INFO(TABLE_NAME,DISPLAY_NAME),params={"embed_models":embed_model_mappings}))





if __name__ == "__main__":
    surreal_edgar_insert()