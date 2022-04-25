import re
from copy import deepcopy
from logging import getLogger

from solarwinds.core.endpoint import Endpoint
from solarwinds.utils import parse_response, sanitize_swdata
from solarwinds.core.exceptions import (
    SWNonUniqueResult,
    SWObjectExists,
    SWObjectNotFound,
    SWObjectPropertyError,
)

logger = getLogger("solarwinds.orion.node")

from datetime import datetime, timedelta

DEFAULT_PROPERTIES = {
    #    "EngineID": 1,
    # "Status": 1,
}

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
    name = 'Node'
    endoint = 'Orion.Nodes'
    _required_attrs = ["ip", "caption"]
    _keys = ['ip', 'caption']
    _exclude_args = []

    def __init__(self, swis, ip=None, caption=None, snmp_version=0, community=None, rw_community=None, engine_id=1,  polling_method='icmp', custom_properties=None, pollers=None):
        self.ip = ip
        self.caption = caption
        self.engine_id = engine_id,
        self.snmp_version = snmp_version
        self.community = community
        self.rw_community = rw_community
        self.polling_method = polling_method
        self.custom_properties = custom_properties
        self.pollers = pollers
        if ip is None and caption is None:
            raise ValueError("Must provide IP, caption, or both.")
        if self.pollers is None:
            self.pollers = DEFAULT_POLLERS[self.polling_method]

    def _get_uri(self):
        if self.ip is not None:
            query = f'SELECT Uri as uri FROM Orion.Nodes WHERE IPAddress = "{self.ip}"'




    def enable_pollers(self):
        node_id = self.get_id()
        for poller_type in self.pollers:
            poller = {
                "PollerType": poller_type,
                "NetObject": f"N:{node_id}",
                "NetObjectType": "N",
                "NetObjectID": node_id,
                "Enabled": True,
            }
            self.swis.create("Orion.Pollers", **poller)
            logger.debug(f"{self.ip}: enable_pollers(): enabled poller {poller_type}")
        return True


    def get_id(self):
        self.id = int(re.search(r"(\d+)$", self.get_uri()).group(0))
        logger.debug(f"{self.ip}: get_id(): got id: {self.id}")
        return self.id

    def remanage(self):
        if self.exists():
            details = self.details()  # TODO: cache this
            if details["properties"]["UnManaged"] is True:
                self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                logger.debug(f"{self.ip}: remanage(): re-managed node")
                return True
            else:
                logger.debug(
                    f"{self.ip}: remanage(): node is already managed, doing nothing"
                )
                return False
        else:
            logger.debug(f"{self.ip}: remanage(): node does not exist, doing nothing")

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
                    "Orion.Nodes", "Unmanage", f"N:{self.id}", start, end, False
                )
                logger.debug(f"{self.ip}: unmanage(): unmanaged node until {end}")
                return True
            else:
                logger.debug(
                    f"{self.ip}: unmanage(): node is already unmanaged, doing nothing"
                )
                return False
        else:
            logger.debug(f"{self.ip}: unmanage(): node does not exist, doing nothing")
            return False

    def update(self, properties=None, custom_properties=None):
        if self.exists():
            if properties is None:
                properties = self.properties
            if custom_properties is None:
                properties = self.custom_properties
            if self.properties is not None or self.custom_properties is not None:
                uri = self.get_uri()
                diff = self.diff()
                if diff:
                    if diff["properties"]:
                        self.swis.update(uri, **diff["properties"])
                        logger.debug(
                            f'{self.ip}: update(): updated properties: {diff["properties"]}'
                        )
                    if diff["custom_properties"]:
                        self.swis.update(
                            f"{uri}/CustomProperties", **diff["custom_properties"]
                        )
                        logger.debug(
                            f'{self.ip}: update(): updated custom properties: {diff["custom_properties"]}'
                        )
                    logger.info(f"{self.ip}: node updated")
                    return True
        else:
            logger.debug(f"{self.ip}: update(): node does not exist, creating")
            return self.create()
