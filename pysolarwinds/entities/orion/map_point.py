from typing import Optional

from pysolarwinds.entities import Entity
from pysolarwinds.exceptions import SWObjectNotFoundError
from pysolarwinds.queries.orion.map_point import QUERY, TABLE
from pysolarwinds.swis import SWISClient


class MapPoint(Entity):
    TYPE = "Orion.WorldMap.Point"
    WRITE_ATTR_MAP = {
        "latitude": "Latitude",
        "longitude": "Longitude",
        "street_address": "StreetAddress",
    }

    def __init__(
        self,
        swis: SWISClient,
        entity: Optional[Entity] = None,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        super().__init__(swis=swis, id=id, uri=uri, data=data, entity=entity)
        self.entity: Entity = entity
        self.latitude: float = self.data.get("Latitude")
        self.longitude: float = self.data.get("Longitude")
        self.street_address: str = self.data.get("StreetAddress")

    def _get_data(self) -> Optional[dict]:
        if self.entity:
            query = QUERY.where(TABLE.InstanceID == self.entity.id)
            if results := self.swis.query(str(query)):
                return results[0]
            else:
                msg = f'No map point exists for entity "{self.entity.name}".'
                raise SWObjectNotFoundError(
                    msg,
                )
        return None

    @property
    def _id(self) -> int:
        return self.data["PointId"]

    @property
    def auto_added(self) -> bool:
        """Whether or not map point was automatically added."""
        return self.data["AutoAdded"]

    @property
    def lat(self) -> float:
        """Convenience property."""
        return self.latitude

    @property
    def lon(self) -> float:
        """Convenience property."""
        return self.longitude

    def __repr__(self) -> str:
        return f"MapPoint(entity={self.entity.__repr__()})"
