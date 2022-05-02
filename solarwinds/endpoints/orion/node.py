from datetime import datetime, timedelta

from orionsdk import SwisClient
from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.worldmap import WorldMapPoint


from solarwinds.defaults import NODE_DEFAULT_POLLERS
from solarwinds.exceptions import SWObjectPropertyError


class OrionNode(Endpoint):
    endpoint = "Orion.Nodes"
    _id_attr = "node_id"
    _swid_key = "NodeID"
    _swquery_attrs = [
        'ip_address',
        'caption'
    ]
    _swargs_attrs = [
        "caption",
        "community",
        "engine_id",
        "ip_address",
        "rw_community",
        "snmp_version",
    ]
    _required_swargs_attrs = [
        "ip_address",
        "engine_id"
    ]
    _child_objects = {
        "map_point": {
            "class": WorldMapPoint,
            "attr_map": {
                "node_id": "instance_id",
                "latitude": "latitude",
                "longitude": "longitude",
            },
        },
    }

    def __init__(
        self,
        swis: SwisClient,
        caption: str = None,
        community: str = None,
        custom_properties: dict = None,
        engine_id: int = 1,
        ip_address: str = None,
        latitude: float = None,
        longitude: float = None,
        node_id: int = None,
        pollers: list = None,
        polling_method: str = None,
        rw_community: str = None,
        snmp_version: int = None,
    ):
        self.swis = swis
        self.caption = caption
        self.community = community
        self.rw_community = rw_community
        self.custom_properties = {} if custom_properties is None else custom_properties
        self.engine_id = engine_id
        self.ip_address = ip_address
        self.latitude = latitude
        self.longitude = longitude
        self.node_id = node_id
        self.polling_method = polling_method or self._get_polling_method()
        self.pollers = pollers or self._get_pollers()
        self.snmp_version = snmp_version or self._get_snmp_version()
        self._extra_swargs = {
            "status": 1,
            "objectsubtype": self.polling_method.upper(),
        }
        if self.ip_address is None and self.caption is None:
            raise SWObjectPropertyError('Must provide either ip_address or caption')
        super().__init__()

    def _get_polling_method(self) -> str:
        if self.community is not None or self.rw_community is not None:
            return 'snmp'
        else:
            return 'icmp'

    def _get_pollers(self) -> list:
        return NODE_DEFAULT_POLLERS[self.polling_method]

    def _get_snmp_version(self) -> int:
        if self.community is not None or self.rw_community is not None:
            return 2
        else:
            return 0

    def _update_object(self, overwrite=False):
        super()._update_object(overwrite=overwrite)
        if self._swdata is not None:
            polling_method = self._swdata["properties"]["ObjectSubType"].lower()
            self.polling_method = polling_method
            self.log.debug(f"polling_method = {polling_method}")
            snmp_version = self._swdata["properties"]["SNMPVersion"]
            self.snmp_version = snmp_version
            self.log.debug(f"snmp_version = {snmp_version}")

    def enable_pollers(self) -> bool:
        node_id = self.node_id or self._get_id()
        for poller_type in self.pollers:
            poller = {
                "PollerType": poller_type,
                "NetObject": f"N:{node_id}",
                "NetObjectType": "N",
                "NetObjectID": node_id,
                "Enabled": True,
            }
            self.swis.create("Orion.Pollers", **poller)
            self.log.info(f"enabled poller {poller_type}")
        return True

    def create(self):
        created = super().create()
        if created is True:
            self.enable_pollers()
        return created

    def remanage(self):
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"] is True:
                self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                self.log.info(f"re-managed node successfully")
                return True
            else:
                self.log.warning(f"node is already managed")
                return False
        else:
            self.log.warning(f"node does not exist, can't remanage")

    def unmanage(self, start=None, end=None):
        if start is None:
            now = datetime.utcnow()
            start = now - timedelta(
                hours=1
            )  # accounts for variance in clock synchronization
        if end is None:
            end = now + timedelta(days=1)
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"] is False:
                self.swis.invoke(
                    "Orion.Nodes", "Unmanage", f"N:{self.node_id}", start, end, False
                )
                self.log.info(f"unmanaged node until {end}")
                return True
            else:
                self.log.warning(f"node is already unmanaged")
                return False
        else:
            self.log.warning(f"node does not exist, can't unmanage")
            return False
