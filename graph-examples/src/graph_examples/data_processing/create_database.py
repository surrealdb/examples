
from surrealdb import Surreal

from graph_examples.helpers import loggers


from graph_examples.helpers.constants import ArgsLoader
from graph_examples.helpers.params import DatabaseParams, SurrealParams

import graph_examples.helpers.constants as constants
# Initialize parameter objects and argument loader
db_params = DatabaseParams()
args_loader = ArgsLoader("Input Embeddings Model",db_params)

"""
Creates a SurrealDB database and namespace, and executes schema DDL.
"""
def surreal_create_database() -> None:
    """
    Initializes and configures a SurrealDB database for Wikipedia embeddings.

    This function performs the following steps:
    1.  Parses command-line arguments using ArgsLoader.
    2.  Establishes a connection to the SurrealDB server.
    3.  Creates a namespace and database if they do not exist, or removes and recreates the database if it already exists.
    4.  Executes schema definition language (DDL) queries from specified files to define tables and functions.
    5.  Handles any errors encountered during database operations.
    """
    logger = loggers.setup_logger("SurrealCreateDatabase")

    overwrite = False
    args_loader.AddArg("overwrite","o","overwrite","Boolean to delete existing database if true. (default{0})",overwrite)
    args_loader.LoadArgs() # Parse command-line arguments

    if args_loader.AdditionalArgs["overwrite"]["value"]:
        overwrite = str(args_loader.AdditionalArgs["overwrite"]["value"]).lower()in ("true","yes","1")

    logger.info(args_loader.string_to_print())
    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        logger.info("Creating database")
         # SurrealQL query to create namespace and database

        if overwrite:
            query= f"""
                    
                    DEFINE NAMESPACE IF NOT EXISTS {db_params.DB_PARAMS.namespace};
                    USE NAMESPACE {db_params.DB_PARAMS.namespace};
                    REMOVE DATABASE IF EXISTS {db_params.DB_PARAMS.database};
                    DEFINE DATABASE {db_params.DB_PARAMS.database};
                    USE DATABASE {db_params.DB_PARAMS.database};
                """
        else:
            query= f"""
                
                    DEFINE NAMESPACE IF NOT EXISTS {db_params.DB_PARAMS.namespace};
                    USE NAMESPACE {db_params.DB_PARAMS.namespace};
                    DEFINE DATABASE IF NOT EXISTS {db_params.DB_PARAMS.database};
                    USE DATABASE {db_params.DB_PARAMS.database};
                """
        
        logger.info(query)

        # Execute the query and check for errors
        SurrealParams.ParseResponseForErrors(connection.query_raw(
            query
        ))
        logger.info("Database created successfully")
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        
        logger.info("Executing common table DDL")
        # Read the schema DDL that holds the SurQL functions from file
        with open(constants.ADV_TABLES_DDL) as f: 
            surlql_to_execute = f.read()
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))

        
        logger.info("Executing common function DDL")
        # Read the schema DDL that holds the SurQL functions from file
        with open(constants.ADV_FUNCTIONS_DDL) as f: 
            surlql_to_execute = f.read()
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))


if __name__ == "__main__":
    surreal_create_database()