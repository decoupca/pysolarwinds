from typing import List, Union

from httpx._types import VerifyTypes

from pysolarwinds.models.orion import Orion
from pysolarwinds.swis import SWISClient


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


def init(
    hostname: str,
    username: str,
    password: str,
    verify: VerifyTypes = True,
    timeout: float = 30.0,
):
    return SolarWindsClient(
        hostname=hostname,
        username=username,
        password=password,
        verify=verify,
        timeout=timeout,
    )


__all__ = ["SolarWindsClient"]
