from solarwinds.core.model import BaseModel
from solarwinds.endpoints.orion.nodes import OrionNode


class Nodes(BaseModel):
    name = "Nodes"

    def node(self, **kwargs):
        return OrionNode(self.swis, **kwargs)
