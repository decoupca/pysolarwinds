"""Exceptions."""


class SWError(Exception):
    """Base SolarWinds error."""


class SWAlertSuppressionError(SWError):
    """Error with suppressing alerts."""


class SWDiscoveryError(SWError):
    """Error in discovery."""


class SWResourceImportError(SWError):
    """Error importing resources."""


class SWEntityManagementError(SWError):
    """Error managing or un-managing an entity."""


class SWEntityExistsError(SWError):
    """Entity already exists."""


class SWEntityPropertyError(SWError):
    """Error with an entity's property."""


class SWNonUniqueResultError(SWError):
    """Search found more than one result matching criteria."""


class SWISError(SWError):
    """All SWIS API errors."""
