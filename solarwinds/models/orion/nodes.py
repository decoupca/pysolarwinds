from solarwinds.model import BaseModel
from solarwinds.endpoints.orion.nodes import OrionNode


class Nodes(BaseModel):
    name = "Nodes"

    def get(self, **kwargs):
        return OrionNode(self.swis, **kwargs)
