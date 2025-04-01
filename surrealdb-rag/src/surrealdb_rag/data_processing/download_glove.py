"""Download GLoVe pre trained model."""

import zipfile

import wget
import os

from surrealdb_rag.helpers import loggers

import surrealdb_rag.helpers.constants as constants


def download_glove_model() -> None:
    """Extract `glove.6B.txt` to `/data`."""
    logger = loggers.setup_logger("DownloadGloveModel")

    logger.info("Downloading Wikipedia")
    if not os.path.exists("data"):
        os.makedirs("data")
    wget.download(
        url=constants.DEFAULT_GLOVE_URL,
        out=constants.DEFAULT_GLOVE_ZIP_PATH,
    )

    logger.info("Extracting to data directory")
    with zipfile.ZipFile(
        constants.DEFAULT_GLOVE_ZIP_PATH, "r"
    ) as zip_ref:
        zip_ref.extractall("data")

    if not os.path.exists(constants.DEFAULT_GLOVE_PATH):
        raise FileNotFoundError(f"File not found: {constants.DEFAULT_GLOVE_PATH}")

    logger.info("Extracted file successfully. Please check the data directory")

if __name__ == "__main__":
    download_glove_model()
    
