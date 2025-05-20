
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams
import time
from graph_examples.helpers.surreal_dml import SurrealDML

db_params = DatabaseParams()
args_loader = ArgsLoader("Monitor indexes",db_params)

# List of tables to check index status for
TABLES = [
    "firm",
    "firm_alias",
    "signed",
    "is_compliance_officer",
    "custodian_for",
    "master_of_feeder",
    "filing",
    "person",
    "person_alias",]

        

def index_status():
    """
    Monitors the status of indexes in a SurrealDB database until all are ready.

    This function connects to SurrealDB, iterates through a list of tables,
    and checks the status of each index on those tables. It continues to loop
    and check until all indexes are in the "ready" state.  It logs the progress
    and current status of the indexes.
    """
    logger = loggers.setup_logger("SurrealProcess Firm indexes")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        any_pending_indexes = True

        while any_pending_indexes:
            index_info = {}
            any_pending_indexes = False
            for table in TABLES:
                query = f"""
                INFO FOR TABLE {table};
                """
                results = connection.query(query)
                if "indexes" in results:
                    indexes = results["indexes"]
                    for index in indexes:
                        index_query = f"INFO FOR INDEX {index} ON TABLE {table};"
                        index_results = connection.query(index_query)
                        index_info[f"{table}: {index}"] = index_results
                        if(index_info[f"{table}: {index}"]["building"]["status"] != "ready"):
                            any_pending_indexes = True
                            logger.info(f"Index {index} on table {table} is pending")
                else:
                    logger.info(f"Table {table} has no indexes")

            logger.info("Current index status:")


            for index, key in enumerate(index_info):
                print(f"{index} {index_info[key]["building"]["status"]} \t\t, Key: {key}, Value: {index_info[key]}")
                
            # Sleep for a while before checking again
            time.sleep(10)




# --- Main execution block ---
if __name__ == "__main__":
    index_status()
# --- End main execution block ---