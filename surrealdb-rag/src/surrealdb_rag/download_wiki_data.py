"""Download OpenAI Wikipedia data."""

import zipfile

import wget
import os

from surrealdb_rag import loggers

import surrealdb_rag.constants as constants

import pandas as pd
import tqdm



def download_wiki_data() -> None:
    """Extract `vector_database_wikipedia_articles_embedded.csv` to `/data`."""
    logger = loggers.setup_logger("DownloadData")

    logger.info(f"Downloading Wikipedia from {constants.WIKI_URL} to {constants.WIKI_ZIP_PATH}")
    wget.download(
        url=constants.WIKI_URL,
        out=constants.WIKI_ZIP_PATH,
    )

    logger.info(f"Extracting data to {constants.WIKI_ZIP_PATH}")
    with zipfile.ZipFile(
        constants.WIKI_ZIP_PATH, "r"
    ) as zip_ref:
        zip_ref.extractall("data")

    if not os.path.exists(constants.WIKI_PATH):
        raise FileNotFoundError(f"File not found: {constants.WIKI_PATH}")

    logger.info("Extracted file successfully. Please check the data directory")

if __name__ == "__main__":
    download_wiki_data()