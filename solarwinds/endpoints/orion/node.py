from datetime import datetime, timedelta
from logging import NullHandler, getLogger
from typing import Union

from orionsdk import SwisClient
from solarwinds.defaults import NODE_DEFAULT_POLLERS
from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.interface import OrionInterfaces
from solarwinds.endpoints.orion.worldmap import WorldMapPoint
from solarwinds.exceptions import SWObjectPropertyError

log = getLogger(__name__)
log.addHandler(NullHandler())


class OrionNode(Endpoint):
    endpoint = "Orion.Nodes"
    _id_attr = "node_id"
    _swid_key = "NodeID"
    _swquery_attrs = ["ip_address", "caption"]
    _swargs_attrs = [
        "caption",
        "community",
        "engine_id",
        "ip_address",
        "rw_community",
        "snmp_version",
    ]
    _required_swargs_attrs = ["ip_address", "engine_id"]
    _child_objects = {
        "map_point": {
            "class": WorldMapPoint,
            "init_args": {
                "node_id": "instance_id",
            },
            "attr_map": {
                "node_id": "instance_id",
                "latitude": "latitude",
                "longitude": "longitude",
            },
        }
    }

    def __init__(
        self,
        swis: SwisClient,
        ip_address: str = None,
        caption: str = None,
        community: str = None,
        rw_community: str = None,
        custom_properties: dict = None,
        engine_id: int = None,
        latitude: float = None,
        longitude: float = None,
        node_id: int = None,
        pollers: list = None,
        polling_method: str = None,
        snmp_version: int = None,
    ):
        self.swis = swis
        self.caption = caption
        self.engine_id = engine_id
        self.community = community
        self.rw_community = rw_community
        self.custom_properties = custom_properties
        self.ip_address = ip_address
        self.latitude = latitude
        self.longitude = longitude
        self.node_id = node_id
        self.polling_method = polling_method
        self.pollers = pollers
        self.snmp_version = snmp_version
        self.interfaces = OrionInterfaces(self)
        if self.ip_address is None and self.caption is None:
            raise SWObjectPropertyError("Must provide either ip_address or caption")
        super().__init__()

    @property
    def name(self) -> str:
        return self.caption

    @property
    def ip(self) -> Union[str, None]:
        return self.ip_address

    @ip.setter
    def ip(self, ip_address: str) -> None:
        self.ip_address = ip_address

    @property
    def hostname(self) -> Union[str, None]:
        return self.caption

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.caption = hostname

    def _set_defaults(self) -> None:
        if self.polling_method is None:
            if self.community is not None or self.rw_community is not None:
                self.polling_method = "snmp"
                self.snmp_version = 2
            else:
                self.polling_method = "icmp"
                self.snmp_version = 0
        if self.pollers is None:
            self.pollers = NODE_DEFAULT_POLLERS[self.polling_method]

    def _get_attr_updates(self) -> dict:
        """
        Get attribute updates from swdata
        """
        swdata = self._swdata["properties"]
        return {
            "caption": swdata["Caption"],
            "ip_address": swdata["IPAddress"],
            "engine_id": swdata["EngineID"],
            "community": swdata["Community"],
            "rw_community": swdata["RWCommunity"],
            "polling_method": self._get_polling_method(),
            "pollers": self.pollers
            or NODE_DEFAULT_POLLERS[swdata["ObjectSubType"].lower()],
            "snmp_version": swdata["SNMPVersion"],
        }

    def _get_extra_swargs(self) -> None:
        return {
            "status": self._get_swdata_value("Status") or 1,
            "objectsubtype": self._get_polling_method().upper(),
        }

    def _get_polling_method(self) -> str:
        community = self._get_swdata_value("Community") or self.community
        rw_community = self._get_swdata_value("RWCommunity") or self.rw_community
        if community is not None or rw_community is not None:
            return "snmp"
        else:
            return "icmp"

    def _get_pollers(self) -> list:
        return NODE_DEFAULT_POLLERS[self.polling_method]

    def _get_snmp_version(self) -> int:
        if self.community is not None or self.rw_community is not None:
            return 2
        else:
            return 0

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
            log.info(f"enabled poller {poller_type}")
        return True

    def create(self):
        created = super().create()
        if created is True:
            self.enable_pollers()
        return created

    def remanage(self) -> bool:
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"] is True:
                self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                log.info(f"re-managed node successfully")
                return True
            else:
                log.warning(f"node is already managed, doing nothing")
                return False
        else:
            log.warning(f"node does not exist, can't remanage")
            return False

    def unmanage(self, start: datetime = None, end: datetime = None) -> bool:
        if self.exists():
            if start is None:
                now = datetime.utcnow()
                # accounts for variance in clock synchronization
                start = now - timedelta(minutes=10)
            if end is None:
                end = now + timedelta(days=1)
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"] is False:
                self.swis.invoke(
                    "Orion.Nodes", "Unmanage", f"N:{self.node_id}", start, end, False
                )
                log.info(f"unmanaged node until {end}")
                return True
            else:
                log.warning(f"node is already unmanaged, doing nothing")
                return False
        else:
            log.warning(f"node does not exist, can't unmanage")
            return False
