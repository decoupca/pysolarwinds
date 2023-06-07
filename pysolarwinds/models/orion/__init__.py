from pysolarwinds.models.orion.credentials import CredentialsModel
from pysolarwinds.models.orion.nodes import NodesModel
from pysolarwinds.models.orion.worldmap import WorldMapModel
from pysolarwinds.swis import SWISClient


class Orion:
    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis
        self.worldmap = WorldMapModel(swis=swis)
        self.credentials = CredentialsModel(swis=swis)
        self.nodes = NodesModel(swis=swis)
