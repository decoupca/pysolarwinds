from datetime import datetime, timedelta

from solarwinds.core.exceptions import SWObjectPropertyError

from solarwinds.core.endpoint import Endpoint
from solarwinds.endpoints.orion.worldmap import WorldMapPoint

DEFAULT_PROPERTIES = {}

DEFAULT_POLLERS = {
    "icmp": [
        "N.Status.ICMP.Native",
        "N.ResponseTime.ICMP.Native",
    ],
    "snmp": [
        "N.ResponseTime.SNMP.Native",
        "N.Details.SNMP.Generic",
        "N.Uptime.SNMP.Generic",
        "N.Cpu.SNMP.HrProcessorLoad",
        "N.Memory.SNMP.NetSnmpReal",
        "N.AssetInventory.Snmp.Generic",
        "N.Topology_Layer3.SNMP.ipNetToMedia",
        "N.Routing.SNMP.Ipv4CidrRoutingTable",
    ],
}


class Node(Endpoint):
    name = "Node"
    endpoint = "Orion.Nodes"
    _required_attrs = ["ipaddress", "caption"]
    _keys = ["ipaddress", "caption"]
    _exclude_attrs = []
    _child_objects = {
        WorldMapPoint: {
            'init_args': {'instance_id': 'node_id',},
            'local_attr': 'map_point',
            'attr_map': {
                'latitude': 'latitude',
                'longitude': 'longitude',
            },
        },
    }
    map_point = None

    def __init__(
        self,
        swis,
        node_id=None,
        ipaddress=None,
        caption=None,
        snmp_version=0,
        community=None,
        latitude=None,
        longitude=None,
        rw_community=None,
        engine_id=None,
        polling_method="icmp",
        custom_properties=None,
        pollers=None,
    ):
        self.swis = swis
        self.node_id = node_id
        self.ipaddress = ipaddress
        self.caption = caption
        self.engine_id = engine_id
        self.snmp_version = snmp_version
        self.community = community
        self.latitude = latitude
        self.longitude = longitude
        self.rw_community = rw_community
        self.polling_method = polling_method
        self.custom_properties = custom_properties
        self.pollers = pollers
        if self.pollers is None:
            self.pollers = DEFAULT_POLLERS[self.polling_method]
        self._get_logger()

    def enable_pollers(self):
        self.id = self._get_id()
        for poller_type in self.pollers:
            poller = {
                "PollerType": poller_type,
                "NetObject": f"N:{self.id}",
                "NetObjectType": "N",
                "NetObjectID": self.id,
                "Enabled": True,
            }
            self.swis.create("Orion.Pollers", **poller)
            self.logger.debug(f"enable_pollers(): enabled poller {poller_type}")
        return True

    def remanage(self):
        if self.exists():
            details = self.details()  # TODO: cache this
            if details["properties"]["UnManaged"] is True:
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
            details = self.details()
            if details["properties"]["UnManaged"] is False:
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
