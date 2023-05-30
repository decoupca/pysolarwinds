from typing import List, Union

from pysolarwinds.swis import SWISClient
from pysolarwinds.models.orion import Orion
from httpx._types import VerifyTypes


class SolarWindsClient:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify: VerifyTypes = True,
        timeout: float = 30.0,
    ):
        self.swis = SWISClient(
            hostname=hostname,
            username=username,
            password=password,
            verify=verify,
            timeout=timeout,
        )
        self.orion = Orion(self.swis)

    def query(self, query: str) -> List:
        return self.swis.query(query)


def api(
    hostname: str,
    username: str,
    password: str,
    verify: Union[bool, str] = False,
    timeout: int = 60,
):
    return SolarWindsClient(
        hostname=hostname,
        username=username,
        password=password,
        verify=verify,
        timeout=timeout,
    )


__all__ = ["SolarWindsClient"]
