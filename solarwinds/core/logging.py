from logging import NullHandler, getLogger

log = getLogger(__name__)
log.addHandler(NullHandler())
