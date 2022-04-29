from datetime import datetime, timedelta

from solarwinds.core.endpoint import Endpoint
from solarwinds.core.exceptions import SWObjectPropertyError
from solarwinds.endpoints.orion.worldmap import WorldMapPoint
from logging import getLogger, NullHandler

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


class OrionNode(Endpoint):
    endpoint = "Orion.Nodes"
    _id_attr = 'node_id'
    _sw_id_key = 'NodeID'
    _required_attrs = ['ip_address', 'engine_id']
    _swquery_attrs = ["ip_address", "caption"]
    _swargs_attrs = [
        'caption',
        'community',
        'engine_id',
        'ip_address',
        'rw_community',
        'snmp_version',
    ]
    _child_objects = {
        # child object class
        WorldMapPoint: {
            # which attribute in this object to store child object
            "child_attr": "map_point",
            # which attrs of parents to map to child attrs
            "attr_map": {
                "node_id": "instance_id",
                "latitude": "latitude",
                "longitude": "longitude",
            },
        },
    }

    def __init__(
        self,
        swis,
        caption=None,
        community=None,
        custom_properties=None,
        engine_id=1,
        ip_address=None,
        latitude=None,
        longitude=None,
        node_id=None,
        pollers=None,
        polling_method=None,
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
        if self.polling_method is None:
            if self.community is not None or self.rw_community is not None:
                self.polling_method = 'snmp'
                self.snmp_version = 2
            else:
                self.polling_method = 'icmp'
        if self.pollers is None:
            self.pollers = DEFAULT_POLLERS[self.polling_method]
        super().__init__()

    def _get_extra_swargs(self):
        return {
            'objectsubtype': self.polling_method.upper(),
        }

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
            self.log.info(f"enabled poller {poller_type}")
        return True

    def create(self):
        created = super().create()
        if created is True:
            self.enable_pollers()
        return created

    def remanage(self):
        if self.exists():
            self._get_swdata(data='properties')
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
            self._get_swdata(data='properties')
            if self._swdata["properties"]["UnManaged"] is False:
                self.swis.invoke(
                    "Orion.Nodes", "Unmanage", f"N:{self.node_id}", start, end, False
                )
                self.log.info(f"unmanaged node until {end}")
                return True
            else:
                self.log.warning(
                    f"node is already unmanaged"
                )
                return False
        else:
            self.log.warning(f"node does not exist, can't unmanage")
            return False
