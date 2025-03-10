
from surrealdb import Surreal

from surrealdb_rag import loggers


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams

# Initialize parameter objects and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input Embeddings Model",db_params,model_params)


"""
Creates a SurrealDB database and namespace, and executes schema DDL.
"""
def surreal_create_database() -> None:
    """Create SurrealDB database for Wikipedia embeddings."""
    logger = loggers.setup_logger("SurrealCreateDatabase")

    args_loader.LoadArgs() # Parse command-line arguments

    logger.info(args_loader.string_to_print())
    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        logger.info("Creating database")
         # SurrealQL query to create namespace and database
        query= f"""
                
                DEFINE NAMESPACE IF NOT EXISTS {db_params.DB_PARAMS.namespace};
                USE NAMESPACE {db_params.DB_PARAMS.namespace};
                REMOVE DATABASE IF EXISTS {db_params.DB_PARAMS.database};
                DEFINE DATABASE {db_params.DB_PARAMS.database};
                USE DATABASE {db_params.DB_PARAMS.database};
            """
        logger.info(query)

        # Execute the query and check for errors
        SurrealParams.ParseResponseForErrors(connection.query_raw(
            query
        ))
        logger.info("Database created successfully")
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info("Executing common function DDL")

        # Read the schema DDL that holds the SurQL functions from file
        with open("./schema/function_ddl.surql") as f: 
            surlql_to_execute = f.read()
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))

        

if __name__ == "__main__":
    surreal_create_database()