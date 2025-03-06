"""Insert Wikipedia data into SurrealDB."""


from surrealdb import Surreal

from surrealdb_rag import loggers


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams

db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input Embeddings Model",db_params,model_params)
args_loader.LoadArgs()

def surreal_create_database() -> None:
    """Create SurrealDB database for Wikipedia embeddings."""
    logger = loggers.setup_logger("SurrealCreateDatabase")

    logger.info(args_loader.string_to_print())
    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        logger.info("Creating database")
        query= f"""
                
                DEFINE NAMESPACE IF NOT EXISTS {db_params.DB_PARAMS.namespace};
                USE NAMESPACE {db_params.DB_PARAMS.namespace};
                REMOVE DATABASE IF EXISTS {db_params.DB_PARAMS.database};
                DEFINE DATABASE {db_params.DB_PARAMS.database};
                USE DATABASE {db_params.DB_PARAMS.database};
            """
        logger.info(query)
        SurrealParams.ParseResponseForErrors(connection.query_raw(
            query
        ))
        logger.info("Database created successfully")
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info("Executing common DDL")
        with open("./schema/table_ddl.surql") as f: 
            surlql_to_execute = f.read()
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))

        with open("./schema/function_ddl.surql") as f: 
            surlql_to_execute = f.read()
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))

        # match model_params.EMBEDDING_MODEL:
        #     case "OPENAI":
        #         logger.info("Creating DDL for open ai model")
        #         with open("./schema/openai_embedding_ddl.surql") as f:
        #             surlql_to_execute = f.read()
        #             SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))
        #     case "GLOVE":
        #         logger.info("Creating DDL for glove model")
        #         with open("./schema/glove_embedding_ddl.surql") as f:
        #             surlql_to_execute = f.read()
        #             SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))
        #     case _:
        #         raise ValueError("Embedding model must be 'OPENAI' or 'GLOVE'")

if __name__ == "__main__":
    surreal_create_database()