from typing import Optional

from pysolarwinds.endpoints.orion.new_node import OrionNode
from pysolarwinds.models.base import BaseModel


class Nodes(BaseModel):
    def create(self):
        pass

    def list(self):
        pass

    def get(
        self,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        caption: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[OrionNode]:
        if id is None and uri is None and caption is None and ip_address is None:
            raise ValueError(
                "Must provide at least one: id, uri, caption, or ip_address."
            )
        if id:
            return OrionNode(swis=self.swis, id=id)
        if uri:
            return OrionNode(swis=self.swis, uri=uri)
        if caption:
            pass
        if ip_address:
            pass
