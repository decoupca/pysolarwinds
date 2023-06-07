from typing import Optional

from pysolarwinds.endpoints import NewEndpoint


class WorldMapPoint(NewEndpoint):
    _entity_type = "Orion.WorldMap.Point"
    _write_attr_map = {
        "latitude": "Latitude",
        "longitude": "Longitude",
        "street_address": "StreetAddress",
    }

    def __init__(
        self,
        node,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        self.node = node
        super().__init__(
            swis=node.swis, id=id, uri=uri, data=data, instance_id=self.node.id
        )
        self.latitude: float = self.data.get("Latitude")
        self.longitude: float = self.data.get("Longitude")
        self.street_address: str = self.data.get("StreetAddress")

    @property
    def auto_added(self) -> bool:
        """Whether or not map point was automatically added."""
        return self.data["AutoAdded"]
