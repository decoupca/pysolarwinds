from pysolarwinds.endpoints.orion.nodes import Node
from pysolarwinds.endpoints.orion.worldmap import WorldMapPoint
from pysolarwinds.models import BaseModel


class WorldMapModel(BaseModel):
    _entity_class = WorldMapPoint

    def create(
        self, node: Node, latitude: float, longitude: float, street_address: str = ""
    ) -> WorldMapPoint:
        return super().create(
            InstanceID=node.id,
            Latitude=latitude,
            Longitude=longitude,
            StreetAddress=street_address,
        )
