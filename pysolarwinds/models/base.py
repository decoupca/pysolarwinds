from typing import Any

from pysolarwinds.swis import SWISClient


class BaseModel:
    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis

    def all(self) -> Any:
        pass

    def create(self) -> Any:
        pass

    def list(self) -> Any:
        pass

    def get(self) -> Any:
        pass
