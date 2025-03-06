"""Insert Wikipedia data into SurrealDB."""


import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag import loggers


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams
from surrealdb_rag.embeddings import WordEmbeddingModel

import surrealdb_rag.constants as constants

db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input Glove embeddings model",db_params,model_params)
args_loader.LoadArgs()

INSERT_GLOVE_EMBEDDINGS = """
    FOR $row IN $embeddings {
        CREATE embedding_model:[$model,$row.word]  CONTENT {
        word : $row.word,
        model : $model,
        embedding: $row.embedding
        } RETURN NONE;
    };
"""

DELETE_GLOVE_EMBEDDINGS = "DELETE embedding_model WHERE model = $model;"

CHUNK_SIZE = 1000

def surreal_model_insert(model_name,model_path,logger):

    logger.info(f"Reading {model_name} model")
    embeddingModel = WordEmbeddingModel(model_path)
    embeddings_df = pd.DataFrame({'word': embeddingModel.dictionary.keys(), 'embedding': embeddingModel.dictionary.values()})
    total_rows = len(embeddings_df)
    total_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE # ceiling division
    with Surreal(db_params.DB_PARAMS.url) as connection:
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")
        logger.info("Inserting rows into SurrealDB")

        #remove any data from the table
        SurrealParams.ParseResponseForErrors(connection.query_raw(DELETE_GLOVE_EMBEDDINGS))
        with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:

            for i in range(0, total_rows, CHUNK_SIZE):
                chunk = embeddings_df.iloc[i:i + CHUNK_SIZE]

                formatted_rows = [
                    {
                        "word":str(row["word"]),
                        "embedding":row["embedding"].tolist()
                    }
                    for _, row in chunk.iterrows()
                ]

                
                SurrealParams.ParseResponseForErrors(connection.query_raw(
                    INSERT_GLOVE_EMBEDDINGS, params={"embeddings": formatted_rows,"model":model_name}
                ))
                pbar.update(1)

   

def surreal_embeddings_insert() -> None:

    """Main entrypoint to insert glove embedding model into SurrealDB."""
    logger = loggers.setup_logger("SurrealEmbeddingsInsert")

    
    logger.info(args_loader.string_to_print())
    surreal_model_insert("GLOVE",constants.GLOVE_PATH,logger)
    surreal_model_insert("CUST_FASTTEXT",constants.CUSTOM_FS_PATH,logger)



if __name__ == "__main__":
    surreal_embeddings_insert()