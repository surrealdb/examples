"""Download OpenAI Wikipedia data."""

import zipfile

import wget
import os

from surrealdb_rag.helpers import loggers

import surrealdb_rag.helpers.constants as constants


def download_wiki_data() -> None:
    """Extract `vector_database_wikipedia_articles_embedded.csv` to `/data`."""
    logger = loggers.setup_logger("DownloadData")

    logger.info(f"Downloading Wikipedia from {constants.DEFAULT_WIKI_URL} to {constants.DEFAULT_WIKI_ZIP_PATH}")
    wget.download(
        url=constants.DEFAULT_WIKI_URL,
        out=constants.DEFAULT_WIKI_ZIP_PATH,
    )

    logger.info(f"Extracting data to {constants.DEFAULT_WIKI_ZIP_PATH}")
    with zipfile.ZipFile(
        constants.DEFAULT_WIKI_ZIP_PATH, "r"
    ) as zip_ref:
        zip_ref.extractall("data")

    if not os.path.exists(constants.DEFAULT_WIKI_PATH):
        raise FileNotFoundError(f"File not found: {constants.DEFAULT_WIKI_PATH}")

    logger.info("Extracted file successfully. Please check the data directory")

if __name__ == "__main__":
    download_wiki_data()