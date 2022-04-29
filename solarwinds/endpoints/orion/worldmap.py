from logging import NullHandler, getLogger

from solarwinds.core.endpoint import Endpoint
from solarwinds.core.exceptions import SWObjectPropertyError


class WorldMapPoint(Endpoint):
    name = "Point"
    endpoint = "Orion.WorldMap.Point"
    _id_attr = "point_id"
    _sw_id_key = "PointId"
    _swquery_attrs = ["point_id", "instance_id"]
    _swargs_attrs = [
        "instance_id",
        "instance",
        "latitude",
        "longitude",
        "auto_added",
        "street_address",
    ]

    def __init__(
        self,
        swis,
        node=None,
        point_id=None,
        instance_id=None,
        instance="Orion.Nodes",
        latitude=None,
        longitude=None,
        auto_added=False,
        street_address=None,
    ):
        self.swis = swis
        self.node = node
        self.point_id = point_id
        self.instance_id = instance_id
        self.instance = instance
        self.latitude = latitude
        self.longitude = longitude
        self.auto_added = auto_added
        self.street_address = street_address
        if self.instance_id is None:
            if self.node is not None:
                self.instance_id = self.node.id

        super().__init__()


class WorldMapPointLabel(Endpoint):
    pass
