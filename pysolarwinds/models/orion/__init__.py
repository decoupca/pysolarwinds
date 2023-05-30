from pysolarwinds.models.orion.credentials import Credentials
from pysolarwinds.models.orion.nodes import Nodes
from pysolarwinds.models.orion.worldmap import WorldMap
from pysolarwinds.swis import SWISClient


class Orion:
    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis
        self.worldmap = WorldMap(swis=swis)
        self.credentials = Credentials(swis=swis)
        self.nodes = Nodes(swis=swis)
