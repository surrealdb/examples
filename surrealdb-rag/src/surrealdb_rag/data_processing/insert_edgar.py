"""Insert Edgar data into SurrealDB."""

import ast

import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag.helpers import loggers
import surrealdb_rag.helpers.constants as constants

from surrealdb_rag.helpers.llm_handler import EMBED_MODEL_DEFINITIONS



from surrealdb_rag.helpers.constants import ArgsLoader
from surrealdb_rag.helpers.params import DatabaseParams, ModelParams, SurrealParams
from surrealdb_rag.helpers.surreal_dml import SurrealDML

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input EDGAR data",db_params,model_params)



# Chunk size for batch processing
BATCH_SIZE = 100


def count_csv_rows_pandas_chunked(csv_filepath, chunk_size=1000): # Adjust chunk_size as needed
    """
    Counts CSV rows accurately using pandas chunking, handling embedded newlines.

    This function efficiently counts the number of rows in a CSV file by reading it in chunks.
    It's designed to handle CSV files that may contain embedded newlines within fields, which
    can cause incorrect row counts if read line by line.

    Args:
        csv_filepath (str): The path to the CSV file.
        chunk_size (int, optional): The number of rows to read in each chunk. Defaults to 1000.

    Returns:
        int: The total number of rows in the CSV file.
    """
    total_rows = 0
    csv_chunk_iterator = pd.read_csv(csv_filepath, chunksize=chunk_size)
    for chunk_df in csv_chunk_iterator:
        total_rows += len(chunk_df) # Add the number of rows in each chunk
    return total_rows

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
            


def insert_rows(table_name, input_file, total_chunks, using_glove, using_fasttext,incrimental_load):
    """
    Inserts data from a CSV file into a SurrealDB table.

    This function reads the CSV file in chunks, formats the data, and inserts it into the specified
    SurrealDB table. It handles different embedding models (GloVe, FastText) and provides options
    for incremental loading.

    Args:
        table_name (str): The name of the SurrealDB table to insert data into.
        input_file (str): The path to the CSV file containing the data.
        total_chunks (int): The total number of chunks to process (used for progress tracking).
        using_glove (bool): Flag indicating whether GloVe embeddings are used.
        using_fasttext (bool): Flag indicating whether FastText embeddings are used.
        incremental_load (bool): Flag indicating whether to perform an incremental load.
    """
    #schema of the csv
    file_keys = {
        "url":"",
        "company_name":"",
        "cik":"",
        "form":"",
        "accession_no":"",
        "company.ticker_display":"",
        "company.tickers":"",
        "company.exchanges":"",
        "company.description":"",
        "company.category":"",
        "company.industry":"",
        "company.sic":"",
        "company.website":"",
        "filing_date":"",
        "file_path":"",
        "chunk":"",
        "content":"",
        "content_glove_vector":"",
        "content_fasttext_vector":"",
        }.keys()
    

    insert_record_surql = SurrealDML.UPSERT_RECORDS(table_name)
    
    # if incrimental_load:
    #     insert_record_surql = SurrealDML.UPSERT_RECORDS(table_name)
    # else:
    #     insert_record_surql = SurrealDML.INSERT_RECORDS(table_name)

    #with tqdm.tqdm(total=total_chunks, desc="Inserting Batches") as pbar: # Progress bar for batches
    with tqdm.tqdm(total=total_chunks,desc="Inserting Batches") as pbar: # Progress bar for batches
        row_counter = 0 # Track row number for batching
        batch_rows = [] # List to accumulate rows for a batch
        with pd.read_csv(input_file, chunksize=BATCH_SIZE) as csv_chunk_iterator: # Iterate through CSV chunks
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
                                "company_tickers":row["company.tickers"],
                                "company_exchanges":row["company.exchanges"],
                                "company_description": row["company.description"],
                                "company_category": row["company.category"],
                                "company_industry": row["company.industry"],
                                "company_sic": row["company.sic"],
                                "company_website": row["company.website"],
                                "filing_date": row["filing_date"],
                        }
                    }

                            
                    batch_rows.append(formatted_row) # Add formatted row to the batch

                    if row_counter % BATCH_SIZE == 0: # Batch size reached, insert batch
                       insert_chunk_of_rows(insert_record_surql, batch_rows)
                       batch_rows = [] # Clear batch after insert
                       pbar.update(1) # Update progress bar after each batch

            # Insert any remaining rows in the last batch (if less than BATCH_SIZE)
            if batch_rows:
                insert_chunk_of_rows(insert_record_surql, batch_rows)
                batch_rows = [] # Clear batch after insert
                pbar.update(1) # Update progress bar after each batch
               

        



"""Main entrypoint to insert embeddings into SurrealDB."""
def surreal_edgar_insert() -> None:
    """
    Main function to insert EDGAR data into SurrealDB.

    This function reads data from a CSV file, configures the SurrealDB connection,
    and calls the `insert_rows` function to perform the data insertion. It also handles
    command-line arguments for customization, including specifying embedding models and
    incremental loading.
    """
    input_file = constants.DEFAULT_EDGAR_PATH
    table_name = ""
    display_name = ""
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
    args_loader.AddArg("input_file","if","input_file","The path to the csv to insert. (default{0})",input_file)
    args_loader.AddArg("table_name","tn","table_name","The sql table name to load the data into (eg embedded_edgar_10k_2025). (default{0})",table_name)
    args_loader.AddArg("display_name","dn","display_name","The name of the corpus to see when selecting in the ux (eg '10k filings for 2025'). (default{0})",display_name)
    args_loader.AddArg("incrimental_load","il","incrimental_load","do an incremental load? or overwrite entire database?. (default{0})",incrimental_load)

    # Parse command-line arguments
    args_loader.LoadArgs()


    if args_loader.AdditionalArgs["input_file"]["value"]:
        input_file = args_loader.AdditionalArgs["input_file"]["value"]
    
    if args_loader.AdditionalArgs["table_name"]["value"]:
        table_name = args_loader.AdditionalArgs["table_name"]["value"]
    else:
        raise Exception("You must specify a table name with the -tn flag")
    
    if args_loader.AdditionalArgs["display_name"]["value"]:
        display_name = args_loader.AdditionalArgs["display_name"]["value"]
    else:
        raise Exception("You must specify a display name with the -dn flag")

    if args_loader.AdditionalArgs["incrimental_load"]["value"]:
        incrimental_load = str(args_loader.AdditionalArgs["incrimental_load"]["value"]).lower()in ("true","yes","1")



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
        if embed_model not in EMBED_MODEL_DEFINITIONS:
              raise Exception(f"{embed_model} is invalid, You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")
    


    # Create embedding model mappings
    embed_model_mappings = []
    for embed_model in embed_models:
        if embed_model in EMBED_MODEL_DEFINITIONS:
            field_name = EMBED_MODEL_DEFINITIONS[embed_model]["field_name"]
            model_definition = EMBED_MODEL_DEFINITIONS[embed_model]["model_definition"]
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
    


    

    with Surreal(db_params.DB_PARAMS.url) as connection:
        
        logger.info(f"Connecting to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")
        if not incrimental_load:
            logger.info(f"Executting DDL for {table_name}")
            # Read and execute table DDL that creates the tables and indexes if missing
            with open(constants.CORPUS_TABLE_DDL) as f: 
                surlql_to_execute = f.read()
                surlql_to_execute = surlql_to_execute.format(corpus_table = table_name)
                
                SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))
            # Update corpus table information
            logger.info(f"Deleting any existing corpus table info for {table_name}")
            SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.DELETE_CORPUS_TABLE_INFO(table_name),params={"embed_models":embed_model_mappings}))
            # Update corpus table information
            logger.info(f"Updating corpus table info for {table_name}")
            SurrealParams.ParseResponseForErrors( connection.query_raw(SurrealDML.UPDATE_CORPUS_TABLE_INFO(table_name,display_name),params={"embed_models":embed_model_mappings}))



    logger.info("Inserting rows into SurrealDB")
    insert_rows(table_name, input_file, total_chunks, using_glove, using_fasttext, incrimental_load)

            




if __name__ == "__main__":
    surreal_edgar_insert()