"""Download OpenAI Wikipedia data."""

import zipfile

import wget
import os

from surrealdb_rag import loggers

import surrealdb_rag.constants as constants

from surrealdb_rag.embeddings import WordEmbeddingModel

import pandas as pd
import tqdm



def download_data() -> None:
    """Extract `vector_database_wikipedia_articles_embedded.csv` to `/data`."""
    logger = loggers.setup_logger("DownloadData")

    logger.info("Downloading Wikipedia")
 
    logger.info("Extracting to data directory")
    with zipfile.ZipFile(
        constants.WIKI_ZIP_PATH, "r"
    ) as zip_ref:
        zip_ref.extractall("data")

    if not os.path.exists(constants.WIKI_PATH):
        raise FileNotFoundError(f"File not found: {constants.WIKI_PATH}")

    logger.info("Loading Glove embedding model")

    try:
        gloveEmbeddingModel = WordEmbeddingModel(constants.GLOVE_PATH)
    except Exception as e:
        logger.error(f"Error opening embedding model. please check the model file was downloaded using download_glove_model {e}")

    try:
        fastTextEmbeddingModel = WordEmbeddingModel(constants.FS_WIKI_PATH)
    except Exception as e:
        logger.error(f"Error opening embedding model. train the model using train_fastText {e}")

    usecols=[
        "url",
        "title",
        "text",
        "content_vector"
    ]


    logger.info("Loading Wiki data to data frame")
    wiki_records_df = pd.read_csv(constants.WIKI_PATH,usecols=usecols)
    
    logger.info("Processing glove embeddings")
    wiki_records_df['content_glove_vector'] = [gloveEmbeddingModel.sentence_to_vec(x) for x in tqdm.tqdm(wiki_records_df["text"], desc="Processing content glove embeddings")]
    

    logger.info("Processing fast text embeddings")
    wiki_records_df['content_fasttext_vector'] = [fastTextEmbeddingModel.sentence_to_vec(x) for x in tqdm.tqdm(wiki_records_df["text"], desc="Processing content fast text embeddings")]
    

    
    logger.info(f"Backing up file {constants.WIKI_PATH + ".bak"}")
    
    os.rename(constants.WIKI_PATH, constants.WIKI_PATH + ".bak")
    logger.info(f"Saving file {constants.WIKI_PATH}")
    wiki_records_df.to_csv(constants.WIKI_PATH, index=False)  # index=False prevents writing the index


    

    logger.info("Extracted file successfully. Please check the data directory")

if __name__ == "__main__":
    download_data()