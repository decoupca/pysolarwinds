from typing import Optional

from pysolarwinds.entities import Entity
from pysolarwinds.entities.orion.worldmap import WorldMapPoint
from pysolarwinds.models import BaseModel


class WorldMapModel(BaseModel):
    _entity_class = WorldMapPoint

    def get(
        self, id: Optional[int] = None, entity: Optional[Entity] = None
    ) -> WorldMapPoint:
        if not id and not entity:
            raise ValueError("Must provide either id or entity.")
        return WorldMapPoint(swis=self.swis, entity=entity, id=id)

    def create(
        self,
        entity: Entity,
        latitude: float,
        longitude: float,
        street_address: str = "",
    ) -> WorldMapPoint:
        return super().create(
            Instance=entity.TYPE,
            InstanceID=entity.id,
            Latitude=latitude,
            Longitude=longitude,
            StreetAddress=street_address,
        )
