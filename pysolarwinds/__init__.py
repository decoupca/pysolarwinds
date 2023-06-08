from httpx._types import VerifyTypes

from pysolarwinds.models.orion import Orion
from pysolarwinds.swis import SWISClient


class SolarWindsClient:
    """Base class through which we create our SWIS client and access objects."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        verify: VerifyTypes = True,
        timeout: float = 30.0,
    ) -> None:
        self.swis = SWISClient(
            host=host,
            username=username,
            password=password,
            verify=verify,
            timeout=timeout,
        )
        self.orion = Orion(self.swis)

    def query(self, query: str) -> list:
        """Run an arbitrary SWQL query."""
        return self.swis.query(query)

    def __repr__(self) -> str:
        return f"SolarWindsClient(host='{self.host}')"


def client(
    host: str,
    username: str,
    password: str,
    verify: VerifyTypes = True,
    timeout: float = 30.0,
) -> SolarWindsClient:
    """Convenience method to create SolarWindsClient objects.

    Typical usage:

    ```python
    import pysolarwinds
    sw = pysolarwinds.client(...)
    ```
    """
    return SolarWindsClient(
        host=host,
        username=username,
        password=password,
        verify=verify,
        timeout=timeout,
    )


__all__ = [
    "SolarWindsClient",
    "Node",
]
