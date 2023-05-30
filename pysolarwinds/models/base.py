from pysolarwinds.swis import SWISClient


class BaseModel:
    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis

    def all(self):
        pass

    def create(self):
        pass

    def list(self):
        pass

    def get(self):
        pass
