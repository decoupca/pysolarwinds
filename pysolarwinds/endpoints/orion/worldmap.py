from typing import Optional

from pysolarwinds.endpoints import NewEndpoint
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.swis import SWISClient


class WorldMapPoint(NewEndpoint):
    TYPE = "Orion.WorldMap.Point"
    WRITE_ATTR_MAP = {
        "latitude": "Latitude",
        "longitude": "Longitude",
        "street_address": "StreetAddress",
    }
    FIELDS = (
        "PointId",
        "Instance",
        "InstanceID",
        "Latitude",
        "Longitude",
        "AutoAdded",
        "StreetAddress",
        "DisplayName",
        "Description",
        "InstanceType",
        "Uri",
        "InstanceSiteId",
    )

    def __init__(
        self,
        swis: SWISClient,
        entity: Optional[NewEndpoint] = None,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        super().__init__(swis=swis, id=id, uri=uri, data=data, entity=entity)
        self.entity: NewEndpoint = entity
        self.latitude: float = self.data.get("Latitude")
        self.longitude: float = self.data.get("Longitude")
        self.street_address: str = self.data.get("StreetAddress")

    def _get_data(self) -> Optional[dict]:
        if self.entity:
            query = self.QUERY.where(self.TABLE.InstanceID == self.entity.id)
            if results := self.swis.query(query.get_sql()):
                return results[0]
            else:
                raise SWObjectNotFound(
                    f'No map point exists for entity "{self.entity.name}".'
                )

    @property
    def auto_added(self) -> bool:
        """Whether or not map point was automatically added."""
        return self.data["AutoAdded"]
