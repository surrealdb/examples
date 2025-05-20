import pandas as pd
from surrealdb import Surreal
import tqdm
import os

from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers   
from graph_examples.helpers.params import DatabaseParams, SurrealParams

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
args_loader = ArgsLoader("Input FastText embeddings model",db_params)

INSERT_EMBEDDINGS = """
    FOR $row IN $embeddings {
        CREATE type::thing("firm_name_embedding_model",$row.word)  CONTENT {
        word : $row.word,
        embedding: $row.embedding
        } RETURN NONE;
    };
"""

DELETE_EMBEDDINGS = """
DELETE firm_name_embedding_model;
"""


CHUNK_SIZE = 1000 # Size of chunks for batch insertion
"""
The number of embedding vectors to insert in each batch. This can be adjusted to optimize
performance based on the database server's capabilities and network conditions.
"""

def surreal_model_insert(model_path,overwrite,logger):
    """
    Inserts word embeddings from a model file into SurrealDB.

    This function reads a word embedding model file, creates a DataFrame from the word-vector pairs,
    and then inserts the embeddings into SurrealDB in batches. It also updates the embedding model
    definition in the database.

    Args:
        model_trainer (str): Name of the training algorithm (e.g., 'GLOVE', 'FASTTEXT').
        model_version (str): Version of the model (e.g., '300d', 'custom wiki').
        model_path (str): Path to the model file.
        description (str): Description of the embedding model.
        corpus (str): Description of the training data.
        logger (logging.Logger): Logger instance.
    """

    word_dictionary = {}
    with open(model_path, 'r', encoding='utf-8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            vector = np.asarray(values[1:], "float32")
            word_dictionary[word] = vector


    with Surreal(db_params.DB_PARAMS.url) as connection:


        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")


        logger.info(f"Reading model")
        # Load the embedding model
        # Create DataFrame from model data.
        embeddings_df = pd.DataFrame({'word': word_dictionary.keys(), 'embedding': word_dictionary.values()})
        # Calculate number of chunks for batch processing.
        total_rows = len(embeddings_df)
        total_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE  # Calculate number of chunks for batch processing


        logger.info(f"Deleting any rows from model")

        if overwrite:
            # Delete existing embeddings for this particular model
            SurrealParams.ParseResponseForErrors(connection.query_raw(DELETE_EMBEDDINGS))
            logger.info("Inserting rows into SurrealDB")

        with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:
            # Iterate through chunks of data.
            for i in range(0, total_rows, CHUNK_SIZE):
                # Get a chunk of data.
                chunk = embeddings_df.iloc[i:i + CHUNK_SIZE]

                # create an array of dicts to bulk load into surreal
                formatted_rows = [
                    {
                        "word": unescape_token_text_for_txt_file(str(row["word"])),
                        "embedding":row["embedding"].tolist()
                    }
                    for _, row in chunk.iterrows()
                ]

                # Insert the chunk.
                SurrealParams.ParseResponseForErrors(connection.query_raw(
                    INSERT_EMBEDDINGS, params={"embeddings": formatted_rows}
                ))
                # Update progress bar.
                pbar.update(1)



"""Main entrypoint to insert glove embedding model into SurrealDB."""
def insert_firm_ft_model() -> None:

    """Main entrypoint to insert glove embedding model into SurrealDB."""
    logger = loggers.setup_logger("SurrealEmbeddingsInsert")
    overwrite = True
    # Add command-line arguments specific to embedding insertion.
    args_loader.AddArg("overwrite","ow","overwrite","If true delete the model and re-upload. Else exit if model and data exists. (default{0})",overwrite)
    # Parse command-line arguments.
    args_loader.LoadArgs()

  
    if args_loader.AdditionalArgs["overwrite"]["value"]:
        overwrite = str(args_loader.AdditionalArgs["overwrite"]["value"]).lower()in ("true","yes","1")


    # Log the parsed arguments.
    logger.info(args_loader.string_to_print())

    
    # Insert the embedding model.
    surreal_model_insert(os.path.join(FAST_TEXT_DIR, 'model.txt'),overwrite,logger)

    logger.info(f"Model loaded!")

if __name__ == "__main__":
    insert_firm_ft_model()