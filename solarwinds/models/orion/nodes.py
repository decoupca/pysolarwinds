from solarwinds.core.model import BaseModel
from solarwinds.endpoints.orion.nodes import Node


class Nodes(BaseModel):
    name = "Nodes"

    def node(self, **kwargs):
        return Node(self.swis, **kwargs)
