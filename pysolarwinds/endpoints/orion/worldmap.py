from pysolarwinds.endpoint import Endpoint


class WorldMapPoint(Endpoint):
    name = "WorldMapPoint"
    endpoint = "Orion.WorldMap.Point"
    _type = "map_point"
    _id_attr = "point_id"
    _swid_key = "PointId"
    _required_swargs_attrs = ["instance_id"]
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
        api,
        node=None,
        point_id=None,
        instance_id=None,
        instance="Orion.Nodes",
        latitude=None,
        longitude=None,
        auto_added=False,
        street_address=None,
    ):
        self.api = api
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

    def _get_attr_updates(self) -> dict:
        swdata = self._swdata["properties"]
        return {
            "latitude": swdata["Latitude"],
            "longitude": swdata["Longitude"],
            "auto_added": swdata["AutoAdded"],
            "street_address": swdata["StreetAddress"],
        }


class WorldMapPointLabel(Endpoint):
    pass
