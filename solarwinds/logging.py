from logging import getLogger, NullHandler
logger = getLogger('solarwinds').addHandler(NullHandler())
