from logging import Logger, NullHandler, getLogger


def get_logger(name: str) -> Logger:
    logger = getLogger(name)
    logger.addHandler(NullHandler())
    return logger
