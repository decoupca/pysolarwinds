from logging import NullHandler, getLogger

logger = getLogger("solarwinds")
logger.addHandler(NullHandler())
