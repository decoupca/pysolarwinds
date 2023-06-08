"""Logging utilities."""
import logging


def get_logger(name: str) -> logging.Logger:
    """Gets a logger for provided name."""
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger
