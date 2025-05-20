
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     
import os
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams

db_params = DatabaseParams()
args_loader = ArgsLoader("Add indexes",db_params)


        

def process_firm_indexes():
    """
    Processes data to add indexes to firm tables in SurrealDB.

    This function connects to SurrealDB, reads DDL statements from a file,
    and executes them to create indexes.  It handles connection setup,
    error logging, and file processing.
    """
    logger = loggers.setup_logger("SurrealProcess Firm indexes")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)


        logger.info(f"Adding indexes to firm tables if not extist") 

        with open(ADV_APP_SEARCH_INDEX_DDL, 'r') as file:
            while True:
                surlql_to_execute = file.readline()
                if not surlql_to_execute:
                    break

                logger.info( f"Processing {surlql_to_execute}")
                SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))
                # Process the line here (e.g., print, analyze, etc.)
                # print(line, end='') # Example: print each line




# --- Main execution block ---
if __name__ == "__main__":
    process_firm_indexes()
# --- End main execution block ---