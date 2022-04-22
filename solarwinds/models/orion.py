from solarwinds.core.model import BaseModel
from solarwinds.endpoints.orion.nodes import Node


class Orion(BaseModel):
    def node(self, **kwargs):
        return Node(self.swis, **kwargs)
