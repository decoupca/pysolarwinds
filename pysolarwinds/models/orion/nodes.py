from typing import Optional

from pysolarwinds.endpoints.orion.new_node import OrionNode
from pysolarwinds.exceptions import SWNonUniqueResultError
from pysolarwinds.models.base import BaseModel


class Nodes(BaseModel):
    def create(self):
        """Create a new node."""
        pass

    def list(self) -> list:
        """Retrieve a list of nodes based on filtering criteria."""
        return []

    def get(
        self,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        caption: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[OrionNode]:
        """
        Get a single OrionNode.

        You may provide more than one argument, but only one will be used to resolve the node,
        in this order of precedence:
        1. id
        2. uri
        3. caption
        4. ip_address

        Arguments:
            id: ID of node.
            uri: SWIS URI of node.
            caption: Caption (hostname) of node.
            ip_address: IP address of node.

        Returns:
            `OrionNode` if exactly one result was found, `None` otherwise.

        Raises:
            `SWNonUniqueResultError` if more than one result was found.

        """
        if id is None and uri is None and caption is None and ip_address is None:
            raise ValueError(
                "Must provide at least one: id, uri, caption, or ip_address."
            )
        if id:
            return OrionNode(swis=self.swis, id=id)
        if uri:
            return OrionNode(swis=self.swis, uri=uri)
        # TODO: Both of these cases need optimization. As written, they necessitate two API calls:
        #       one to retrieve the URI, and another to fetch data.
        if caption:
            result = self.swis.query(
                f"SELECT Uri FROM Orion.Nodes WHERE Caption = '{caption}'"
            )
            if result:
                if len(result) > 1:
                    raise SWNonUniqueResultError(
                        f'Found {len(result)} results with caption "{caption}".'
                    )
                return OrionNode(swis=self.swis, uri=result[0]["Uri"])
        if ip_address:
            result = self.swis.query(
                f"SELECT Uri FROM Orion.Nodes WHERE IPAddress = '{ip_address}'"
            )
            if result:
                if len(result) > 1:
                    raise SWNonUniqueResultError(
                        f'Found {len(result)} results with ip_address "{ip_address}".'
                    )
                return OrionNode(swis=self.swis, uri=uri)
