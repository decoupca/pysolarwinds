"""SolarWindsClient nodes model."""
from typing import Optional, Union

from pysolarwinds.entities.orion.nodes import Node
from pysolarwinds.models.base import BaseModel
from pysolarwinds.queries.orion.nodes import QUERY, TABLE


class NodesModel(BaseModel):
    """SolarWindsClient nodes model."""

    def list(
        self,
        caption: Union[str, list[str], None] = None,  # noqa
        vendor: Optional[str] = None,
        status: Union[int, str, None] = None,
        query: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list:
        """Retrieve a list of nodes based on filtering criteria."""
        if query:
            return [
                Node(
                    swis=self.swis,
                    id=x.get("NodeID"),
                    uri=x.get("Uri"),
                    caption=x.get("Caption"),
                    ip_address=x.get("IPAddress"),
                )
                for x in self.swis.query(query)
            ]
        query = QUERY
        if vendor:
            query = QUERY.where(TABLE.vendor == vendor)
        if status:
            query = QUERY.where(TABLE.status == status)
        if limit:
            query = QUERY.top(limit)
        result = self.swis.query(str(query))
        return [Node(swis=self.swis, data=x) for x in result]

    def get(
        self,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        caption: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Node:
        """Get a single Node.

        You may provide more than one argument, but only one will be used to resolve the node,
        in this order of precedence:
        1. id
        2. uri
        3. caption
        4. ip_address

        Args:
            id: ID of node.
            uri: SWIS URI of node.
            caption: Caption (hostname) of node.
            ip_address: IP address of node.

        Returns:
            `Node` if exactly one result was found.

        Raises:
            None.

        """
        if id is None and uri is None and caption is None and ip_address is None:
            msg = "Must provide at least one: id, uri, caption, or ip_address."
            raise ValueError(
                msg,
            )
        return Node(
            swis=self.swis,
            id=id,
            uri=uri,
            caption=caption,
            ip_address=ip_address,
        )
