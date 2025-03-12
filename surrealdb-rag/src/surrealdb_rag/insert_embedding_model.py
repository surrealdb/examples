"""Insert Wikipedia data into SurrealDB."""


import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag import loggers


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams
from surrealdb_rag.embeddings import WordEmbeddingModel

import surrealdb_rag.constants as constants


# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input Glove embeddings model",db_params,model_params)

# SurrealQL queries for database operations
INSERT_EMBEDDINGS = """
    LET $model = type::thing('embedding_model_definition',[$model_trainer,$model_version]);
    FOR $row IN $embeddings {
        CREATE embedding_model:[$model,$row.word]  CONTENT {
        word : $row.word,
        model : $model,
        embedding: $row.embedding
        } RETURN NONE;
    };
"""

DELETE_EMBEDDINGS = """
LET $model = type::thing('embedding_model_definition',[$model_trainer,$model_version]);
DELETE embedding_model WHERE model = $model;
"""


UPDATE_EMBEDDING_MODEL_DEF = """
LET $model = type::thing('embedding_model_definition',[$model_trainer,$model_version]);
UPSERT embedding_model_definition:[$model_trainer,$model_version] CONTENT {
    model_trainer:$model_trainer,
    host:'SQL',
    dimensions:$dimensions, 
    version:$model_version, 
    corpus:$corpus, 
    description:$description
};
"""


CHUNK_SIZE = 1000 # Size of chunks for batch insertion

"""
Inserts word embeddings from a model file into SurrealDB.

Args:
    model_trainer (str): Name of the training algorithm (e.g., 'GLOVE', 'FASTTEXT').
    model_version (str): Version of the model (e.g., '300d', 'custom wiki').
    model_path (str): Path to the model file.
    description (str): Description of the embedding model.
    corpus (str): Description of the training data.
    logger (logging.Logger): Logger instance.
"""
def surreal_model_insert(model_trainer,model_version,model_path,description,corpus,logger):

    logger.info(f"Reading {model_trainer} {model_version} model")
     # Load the embedding model
    embeddingModel = WordEmbeddingModel(model_path, model_trainer=="FASTTEXT") 
    # Create DataFrame from model data.
    embeddings_df = pd.DataFrame({'word': embeddingModel.dictionary.keys(), 'embedding': embeddingModel.dictionary.values()})
    # Calculate number of chunks for batch processing.
    total_rows = len(embeddings_df)
    total_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE  # Calculate number of chunks for batch processing
    with Surreal(db_params.DB_PARAMS.url) as connection:
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")
        logger.info(f"Deleting any rows from {model_trainer} {model_version}")

        # Delete existing embeddings for this particular model
        SurrealParams.ParseResponseForErrors(connection.query_raw(DELETE_EMBEDDINGS,params={"model_trainer":model_trainer,"model_version":model_version}))
        logger.info("Inserting rows into SurrealDB")

        with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:
            # Iterate through chunks of data.
            for i in range(0, total_rows, CHUNK_SIZE):
                # Get a chunk of data.
                chunk = embeddings_df.iloc[i:i + CHUNK_SIZE]

                # create an array of dicts to bulk load into surreal
                formatted_rows = [
                    {
                        "word": WordEmbeddingModel.unescape_token_text_for_txt_file(str(row["word"])),
                        "embedding":row["embedding"].tolist()
                    }
                    for _, row in chunk.iterrows()
                ]

                # Insert the chunk.
                SurrealParams.ParseResponseForErrors(connection.query_raw(
                    INSERT_EMBEDDINGS, params={"embeddings": formatted_rows,"model_trainer":model_trainer,"model_version":model_version}
                ))
                # Update progress bar.
                pbar.update(1)

        # Update the model definition.
        SurrealParams.ParseResponseForErrors(connection.query_raw(UPDATE_EMBEDDING_MODEL_DEF,
                                                                  params={
                                                                      "model_trainer":model_trainer,
                                                                      "model_version":model_version,
                                                                      "dimensions":embeddingModel.vector_size,
                                                                      "version":model_version,
                                                                      "description":description,
                                                                      "corpus":corpus
                                                                  }))
                


"""Main entrypoint to insert glove embedding model into SurrealDB."""
def surreal_embeddings_insert() -> None:

    """Main entrypoint to insert glove embedding model into SurrealDB."""
    logger = loggers.setup_logger("SurrealEmbeddingsInsert")

    # Add command-line arguments specific to embedding insertion.
    args_loader.AddArg(
        "model_trainer","emtr","model_trainer","The name of the training algorithm: 'GLOVE' or 'FASTTEXT' (Default{0})",None
        )    
    args_loader.AddArg(
        "model_version","emv","model_version","The name of the version of the model: eg '300d' or 'custom wiki'  (Default{0})",None
        )
    args_loader.AddArg(
        "model_path","emp","model_path","The path to the txt file with the words and vectors 'data/glove.6B.300d.txt' or 'data/custom_wiki_fast_text.txt'  (Default{0})",None
        )
    args_loader.AddArg(
        "description","des","description","a description of the embedding model. Include source and other notes (Default{0})",None
        )
    args_loader.AddArg(
        "corpus","cor","corpus","a description of the embedding model training data. (Default{0})",None
        )

    # Parse command-line arguments.
    args_loader.LoadArgs()


    # Retrieve argument values.

    model_trainer = args_loader.AdditionalArgs["model_trainer"]["value"]
    if not model_trainer or not model_trainer in ['GLOVE','FASTTEXT']:
        raise Exception("You must supply a model trainer with -emtr and it must be 'GLOVE' or 'FASTTEXT' ")
    model_version = args_loader.AdditionalArgs["model_version"]["value"]
    if not model_version:
        raise Exception("You must supply a model version")
    model_path = args_loader.AdditionalArgs["model_path"]["value"]
    if not model_path:
        raise Exception("You must supply a model path")
    description = args_loader.AdditionalArgs["description"]["value"]
    if not description:
        raise Exception("You must supply a model description")
    corpus = args_loader.AdditionalArgs["corpus"]["value"]
    if not description:
        raise Exception("You must supply a model corpus")


    # Log the parsed arguments.
    logger.info(args_loader.string_to_print())

    
    # Insert the embedding model.
    surreal_model_insert(model_trainer,model_version,model_path,description,corpus,logger)

    logger.info(f"Model loaded!")

if __name__ == "__main__":
    surreal_embeddings_insert()