"""Map point model."""
from typing import Optional

from pysolarwinds.entities import Entity
from pysolarwinds.entities.orion.map_point import MapPoint
from pysolarwinds.models import BaseModel


class MapPointsModel(BaseModel):
    """Map point model."""

    _entity_class = MapPoint

    def get(
        self,
        id: Optional[int] = None,
        entity: Optional[Entity] = None,
    ) -> MapPoint:
        """Get a map point.

        Args:
            id: Map point ID to retrieve.
            entity: Entity for which to retrieve a map point.

        Returns:
            MapPoint object.

        Raises:
            `ValueError` if neither id nor entity is provided.

        """
        if not id and not entity:
            msg = "Must provide either id or entity."
            raise ValueError(msg)
        return MapPoint(swis=self.swis, entity=entity, id=id)

    def create(
        self,
        entity: Entity,
        latitude: float,
        longitude: float,
        street_address: str = "",
    ) -> MapPoint:
        """Create a map point.

        Args:
            entity: Parent SWIS entity for map point.
            latitude: Latitude for coords.
            longitude: Longitude for coords.
            street_address: Optional street address.

        Returns:
            MapPoint object.

        Raises:
            None.
        """
        return super().create(
            Instance=entity.TYPE,
            InstanceID=entity.id,
            Latitude=latitude,
            Longitude=longitude,
            StreetAddress=street_address,
        )
