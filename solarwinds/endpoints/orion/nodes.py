from datetime import datetime, timedelta

from solarwinds.core.endpoint import Endpoint
from solarwinds.core.exceptions import SWObjectPropertyError
from solarwinds.endpoints.orion.worldmap import WorldMapPoint

DEFAULT_PROPERTIES = {}

DEFAULT_POLLERS = {
    "icmp": [
        "N.Status.ICMP.Native",
        "N.ResponseTime.ICMP.Native",
    ],
    "snmp": [
        "N.AssetInventory.Snmp.Generic",
        "N.Cpu.SNMP.HrProcessorLoad",
        "N.Details.SNMP.Generic",
        "N.Memory.SNMP.NetSnmpReal",
        "N.ResponseTime.SNMP.Native",
        "N.Routing.SNMP.Ipv4CidrRoutingTable",
        "N.Topology_Layer3.SNMP.ipNetToMedia",
        "N.Uptime.SNMP.Generic",
    ],
}


class Node(Endpoint):
    name = "Node"
    endpoint = "Orion.Nodes"
    _required_attrs = ["ip_address", "caption"]
    _keys = ["ip_address", "caption"]
    _exclude_attrs = []
    _child_objects = {
        WorldMapPoint: {
            "init_args": {
                "instance_id": "node_id",
            },
            "local_attr": "map_point",
            "attr_map": {
                "latitude": "latitude",
                "longitude": "longitude",
            },
        },
    }
    map_point = None

    def __init__(
        self,
        swis,
        caption=None,
        community=None,
        custom_properties=None,
        engine_id=None,
        ip_address=None,
        latitude=None,
        longitude=None,
        node_id=None,
        pollers=None,
        polling_method="icmp",
        rw_community=None,
        snmp_version=0,
    ):
        self.swis = swis
        self.caption = caption
        self.community = community
        self.custom_properties = custom_properties
        self.engine_id = engine_id
        self.ip_address = ip_address
        self.latitude = latitude
        self.longitude = longitude
        self.node_id = node_id
        self.pollers = pollers
        self.polling_method = polling_method
        self.rw_community = rw_community
        self.snmp_version = snmp_version
        if self.pollers is None:
            self.pollers = DEFAULT_POLLERS[self.polling_method]
        self._get_logger()

    def enable_pollers(self):
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
            self.logger.debug(f"enable_pollers(): enabled poller {poller_type}")
        return True

    def remanage(self):
        if self.exists():
            self._get_swdata(data='properties')
            if self._swdata["properties"]["UnManaged"] is True:
                self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                self.logger.debug(f"remanage(): re-managed node")
                return True
            else:
                self.logger.debug(f"remanage(): node is already managed, doing nothing")
                return False
        else:
            self.logger.debug(f"remanage(): node does not exist, doing nothing")

    def unmanage(self, start=None, end=None):
        if start is None:
            now = datetime.utcnow()
            start = now - timedelta(
                hours=1
            )  # accounts for variance in clock synchronization
        if end is None:
            end = now + timedelta(days=1)
        if self.exists():
            self._get_swdata(data='properties')
            if self._swdata["properties"]["UnManaged"] is False:
                self.swis.invoke(
                    "Orion.Nodes", "Unmanage", f"N:{self.node_id}", start, end, False
                )
                self.logger.debug(f"unmanage(): unmanaged node until {end}")
                return True
            else:
                self.logger.debug(
                    f"unmanage(): node is already unmanaged, doing nothing"
                )
                return False
        else:
            self.logger.debug(f"unmanage(): node does not exist, doing nothing")
            return False
