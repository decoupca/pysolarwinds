from typing import Optional

from pysolarwinds.entities import Entity
from pysolarwinds.entities.orion.map_point import MapPoint
from pysolarwinds.models import BaseModel


class MapPointsModel(BaseModel):
    _entity_class = MapPoint

    def get(
        self, id: Optional[int] = None, entity: Optional[Entity] = None
    ) -> MapPoint:
        if not id and not entity:
            raise ValueError("Must provide either id or entity.")
        return MapPoint(swis=self.swis, entity=entity, id=id)

    def create(
        self,
        entity: Entity,
        latitude: float,
        longitude: float,
        street_address: str = "",
    ) -> MapPoint:
        return super().create(
            Instance=entity.TYPE,
            InstanceID=entity.id,
            Latitude=latitude,
            Longitude=longitude,
            StreetAddress=street_address,
        )
