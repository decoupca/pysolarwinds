from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.endpoints.orion.node import OrionNode
from solarwinds.models.orion.worldmap import WorldMap


class Orion(object):
    def __init__(self, swis):
        self.swis = swis
        self.worldmap = WorldMap(swis)

    def credential(self, **kwargs):
        return OrionCredential(self.swis, **kwargs)

    def node(self, **kwargs):
        return OrionNode(self.swis, **kwargs)
