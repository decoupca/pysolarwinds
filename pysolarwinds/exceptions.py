class SWError(Exception):
    """Base SolarWinds SWError."""

    pass


class SWAlertSuppressionError(SWError):
    pass


class SWDiscoveryError(SWError):
    pass


class SWResourceImportError(SWError):
    pass


class SWObjectManageError(SWError):
    pass


class SWIDNotFound(SWError):
    pass


class SWUriNotFound(SWError):
    pass


class SWObjectNotFound(SWError):
    pass


class SWObjectExists(SWError):
    pass


class SWObjectDoesNotExist(SWError):
    pass


class SWObjectPropertyError(SWError):
    pass


class SWNonUniqueResultError(SWError):
    pass


class SWObjectCreationError(SWError):
    pass


class SWISError(SWError):
    """All SWIS API errors."""

    pass
