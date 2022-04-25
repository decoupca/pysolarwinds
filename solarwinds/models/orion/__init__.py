from solarwinds.models.orion.worldmap import WorldMap
from solarwinds.models.orion.nodes import Nodes


class Orion(object):
    def __init__(self, swis):
        self.nodes = Nodes(swis)
        self.worldmap = WorldMap(swis)
