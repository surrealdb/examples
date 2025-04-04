"""Download OpenAI Wikipedia data."""

import zipfile

import wget
import os

from surrealdb_rag.helpers import loggers

import surrealdb_rag.helpers.constants as constants


def download_wiki_data() -> None:
    """
    Downloads and extracts the Wikipedia articles dataset.

    This function downloads a zipped file containing Wikipedia articles from a specified URL,
    extracts the `vector_database_wikipedia_articles_embedded.csv` file, and places it in the `/data` directory.
    It also includes error handling for file extraction.

    Args:
        None

    Returns:
        None

    Raises:
        FileNotFoundError: If the extracted Wikipedia articles file is not found after extraction.
    """
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