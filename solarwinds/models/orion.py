from solarwinds.core.model import BaseModel
from solarwinds.endpoints.orion.nodes import Node
from solarwinds.endpoints.orion.worldmap import Point, PointLabel


class Orion(BaseModel):
    def node(self, **kwargs):
        return Node(self.swis, **kwargs)
