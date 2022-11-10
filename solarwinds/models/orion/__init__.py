from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.endpoints.orion.node import OrionNode
from solarwinds.models.orion.worldmap import WorldMap


class Orion(object):
    def __init__(self, api):
        self.api = api
        self.worldmap = WorldMap(api)

    def credential(self, **kwargs) -> OrionCredential:
        return OrionCredential(self.api, **kwargs)

    def node(self, **kwargs) -> OrionNode:
        return OrionNode(self.api, **kwargs)
