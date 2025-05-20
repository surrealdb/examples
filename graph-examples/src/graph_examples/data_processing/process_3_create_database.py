
from surrealdb import Surreal

from graph_examples.helpers import loggers


from graph_examples.helpers.constants import ArgsLoader
from graph_examples.helpers.params import DatabaseParams, SurrealParams

import graph_examples.helpers.constants as constants
# Initialize parameter objects and argument loader
db_params = DatabaseParams()
args_loader = ArgsLoader("Create database",db_params)


def surreal_create_database() -> None:
    """
    Creates a SurrealDB database and defines necessary tables and functions.

    This function connects to SurrealDB, creates a namespace and database (optionally deleting
    existing ones if the 'overwrite' flag is set), and then executes SurrealQL
    scripts to define common tables and functions.
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