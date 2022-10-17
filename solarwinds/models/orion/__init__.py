from solarwinds.endpoints.orion.node import OrionNode, OrionNodes
from solarwinds.models.orion.worldmap import WorldMap


class Orion(object):
    def __init__(self, swis):
        self.swis = swis
        self.worldmap = WorldMap(swis)

    def node(self, **kwargs):
        return OrionNode(self.swis, **kwargs)

    def nodes(self, **kwargs):
        return OrionNodes(self.swis, **kwargs)
