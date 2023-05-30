from typing import List, Union

from pysolarwinds.api import API
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
    return pysolarwinds(
        hostname=hostname,
        username=username,
        password=password,
        verify=verify,
        timeout=timeout,
    )


__all__ = ["pysolarwinds"]
