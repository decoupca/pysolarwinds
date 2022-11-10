from typing import List, Union

from solarwinds.api import API
from solarwinds.models.orion import Orion


class SolarWinds:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify: Union[bool, str] = False,
        timeout: int = 60,
    ):
        self.api = API(
            hostname=hostname,
            username=username,
            password=password,
            verify=verify,
            timeout=timeout,
        )
        self.orion = Orion(self.api)

    def query(self, query: str) -> List:
        return self.api.query(query)


def api(
    hostname: str,
    username: str,
    password: str,
    verify: Union[bool, str] = False,
    timeout: int = 60,
):
    return SolarWinds(
        hostname=hostname,
        username=username,
        password=password,
        verify=verify,
        timeout=timeout,
    )


__all__ = ["SolarWinds"]
