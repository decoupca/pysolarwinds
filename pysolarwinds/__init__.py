from typing import List, Union

from pysolarwinds.client import SWISClient
from pysolarwinds.models.orion import Orion


class pysolarwinds:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify: Union[bool, str] = False,
        timeout: int = 60,
    ):
        self.client = SWISClient(
            hostname=hostname,
            username=username,
            password=password,
            verify=verify,
            timeout=timeout,
        )
        self.orion = Orion(self.client)

    def query(self, query: str) -> List:
        return self.client.query(query)


def api(
    hostname: str,
    username: str,
    password: str,
    verify: Union[bool, str] = False,
    timeout: int = 60,
):
    return pysolarwinds(
        hostname=hostname,
        username=username,
        password=password,
        verify=verify,
        timeout=timeout,
    )


__all__ = ["pysolarwinds"]
