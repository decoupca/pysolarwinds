class SWError(Exception):
    """Base SolarWinds SWError."""


class SWAlertSuppressionError(SWError):
    pass


class SWDiscoveryError(SWError):
    pass


class SWResourceImportError(SWError):
    pass


class SWObjectManageError(SWError):
    pass


class SWIDNotFoundError(SWError):
    pass


class SWObjectNotFoundError(SWError):
    pass


class SWObjectExistsError(SWError):
    pass


class SWObjectPropertyError(SWError):
    pass


class SWNonUniqueResultError(SWError):
    pass


class SWObjectCreationError(SWError):
    pass


class SWISError(SWError):
    """All SWIS API errors."""
