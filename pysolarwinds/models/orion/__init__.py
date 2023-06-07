from pysolarwinds.models.orion.credentials import CredentialsModel
from pysolarwinds.models.orion.map_point import MapPointsModel
from pysolarwinds.models.orion.nodes import NodesModel
from pysolarwinds.swis import SWISClient


class Orion:
    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis
        self.map_points = MapPointsModel(swis=swis)
        self.credentials = CredentialsModel(swis=swis)
        self.nodes = NodesModel(swis=swis)

    @property
    def creds(self) -> CredentialsModel:
        """Convenience property."""
        return self.credentials
