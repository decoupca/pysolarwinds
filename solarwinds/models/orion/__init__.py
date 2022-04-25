from solarwinds.models.orion.nodes import Nodes
from solarwinds.models.orion.worldmap import WorldMap


class Orion(object):
    def __init__(self, swis):
        self.nodes = Nodes(swis)
        self.worldmap = WorldMap(swis)
