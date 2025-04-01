
import os

from surrealdb_rag.helpers import loggers

import surrealdb_rag.helpers.constants as constants

from surrealdb_rag.data_processing.embeddings import WordEmbeddingModel

import pandas as pd
import tqdm


def append_wiki_vectors() -> None:
    logger = loggers.setup_logger("DownloadData")

    if not os.path.exists(constants.DEFAULT_WIKI_PATH):
        raise FileNotFoundError(f"File not found: {constants.DEFAULT_WIKI_PATH}")

    logger.info(f"Loading Glove embedding model {constants.DEFAULT_GLOVE_PATH}")
    try:
        gloveEmbeddingModel = WordEmbeddingModel(constants.DEFAULT_GLOVE_PATH,False)
    except Exception as e:
        logger.error(f"Error opening embedding model. please check the model file was downloaded using download_glove_model {e}")

    logger.info(f"Loading custom FastText embedding model {constants.DEFAULT_FS_WIKI_PATH}")
    try:
        fastTextEmbeddingModel = WordEmbeddingModel(constants.DEFAULT_FS_WIKI_PATH,True)
    except Exception as e:
        logger.error(f"Error opening embedding model. train the model using train_fastText {e}")

    usecols=[
        "url",
        "title",
        "text",
        "content_vector"
    ]


    logger.info("Loading Wiki data to data frame")
    wiki_records_df = pd.read_csv(constants.DEFAULT_WIKI_PATH,usecols=usecols)
    
    logger.info("Processing glove embeddings")
    wiki_records_df['content_glove_vector'] = [gloveEmbeddingModel.sentence_to_vec(x) for x in tqdm.tqdm(wiki_records_df["text"], desc="Processing content glove embeddings")]
    
    logger.info("Processing fast text embeddings")
    wiki_records_df['content_fasttext_vector'] = [fastTextEmbeddingModel.sentence_to_vec(x) for x in tqdm.tqdm(wiki_records_df["text"], desc="Processing content fast text embeddings")]
    
    logger.info(f"Backing up file {constants.DEFAULT_WIKI_PATH + ".bak"}")
    
    os.rename(constants.DEFAULT_WIKI_PATH, constants.DEFAULT_WIKI_PATH + ".bak")
    logger.info(f"Saving file {constants.DEFAULT_WIKI_PATH}")
    wiki_records_df.to_csv(constants.DEFAULT_WIKI_PATH, index=False)  # index=False prevents writing the index

    logger.info("Appended vectors successfully. Please check the data directory")

if __name__ == "__main__":
    append_wiki_vectors()