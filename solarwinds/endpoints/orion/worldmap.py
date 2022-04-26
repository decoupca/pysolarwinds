from solarwinds.core.endpoint import Endpoint
from solarwinds.core.exceptions import SWObjectPropertyError


class Point(Endpoint):
    name = "Point"
    endpoint = "Orion.WorldMap.Point"
    _required_attrs = ["node", "instance_id"]
    _keys = ["instance_id"]
    _exclude_attrs = ["node"]

    def __init__(
        self,
        swis,
        node=None,
        instance_id=None,
        instance="Orion.Nodes",
        latitude=None,
        longitude=None,
        auto_added=False,
        street_address=None,
    ):
        self.swis = swis
        self.node = node
        self.instance_id = instance_id
        self.instance = instance
        self.latitude = latitude
        self.longitude = longitude
        self.auto_added = auto_added
        self.street_address = street_address
        if self.instance_id is None:
            if self.node is None:
                return SWObjectPropertyError("Must provide either node or instance_id")
            else:
                self.instance_id = self.node.id
        self._get_logger()

class PointLabel(Endpoint):
    pass
