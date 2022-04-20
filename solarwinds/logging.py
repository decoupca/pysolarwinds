from logging import getLogger, NullHandler
logger = getLogger('solarwinds')
logger.addHandler(NullHandler())
