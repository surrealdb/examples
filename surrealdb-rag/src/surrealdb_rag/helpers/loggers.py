"""Module to configure logging."""

import logging


def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger with the given name.

    Args:
        name: Name of the logger.

    Returns:
        Configured Python logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
