import re
from copy import deepcopy
from logging import getLogger

from solarwinds.core.endpoint import Endpoint

from solarwinds.core.exceptions import (SWNonUniqueResult, SWObjectExists,
                                        SWObjectNotFound,
                                        SWObjectPropertyError)

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
    def __init__(self, module, ip=None, hostname=None, **kwargs):
        super().__init__(module)
        self.ip = None
        self.hostname = None
        self.id = None
        self.uri = None
        self.properties = kwargs.get("properties")
        self.custom_properties = kwargs.get("custom_properties")
        self.snmpv2c = kwargs.get("snmpv2c")
        if ip is None:
            if self.properties is not None:
                self.ip = self.properties.get("ip")
        else:
            self.ip = ip
        if hostname is None:
            if self.properties is not None:
                self.hostname = self.properties.get("hostname")
        else:
            self.hostname = hostname
        if ip is None and hostname is None:
            raise ValueError("Must provide IP, hostname, or both.")

        # default properties
        defaults = deepcopy(DEFAULT_PROPERTIES)
        if self.properties:
            defaults.update(self.properties)
        self.properties = defaults
        self.properties["IPAddress"] = self.ip
        if self.hostname:
            self.properties["Caption"] = self.hostname

        # polling method
        self.polling_method = self.properties.get("ObjectSubType")
        if self.polling_method:
            self.polling_method = self.polling_method.lower()
        else:
            if self.snmpv2c is None:
                self.polling_method = "icmp"
                self.properties["ObjectSubType"] = "ICMP"
            else:
                self.polling_method = "snmp"
                self.properties["ObjectSubType"] = "SNMP"

        # pollers
        self.pollers = self.properties.get("pollers")
        if self.pollers is None:
            self.pollers = DEFAULT_POLLERS[self.polling_method]

        # snmpv2c
        if self.snmpv2c is not None:
            self.properties["SNMPVersion"] = 2
            community = self.snmpv2c.get("rw") or self.snmpv2c.get("ro")
            if community is not None and self.polling_method == "snmp":
                self.properties["Community"] = community

    def create(self, properties=None, custom_properties=None):
        if properties is None:
            properties = self.properties
        if custom_properties is None:
            custom_properties = self.custom_properties
        if properties is None:
            raise ValueError("Must provide properties to create node.")
        if self.exists():
            # TODO: implement overwrite/re-create option
            raise SWObjectExists(f"Node with IP {self.ip} already exists.")
        if not properties.get("EngineID"):
            properties["EngineID"] = 1
        self.uri = self.swis.create("Orion.Nodes", **properties)
        if self.custom_properties:
            self.update(custom_properties=custom_properties)
        if self.pollers:
            self.enable_pollers()
        logger.info(f"{self.ip}: node created")
        return True

    def delete(self):
        self.swis.delete(self.get_uri())
        self.uri = None
        self.id = None
        logger.info(f"{self.ip}: node deleted")
        return True

    def details(self, force=False):
        uri = self.get_uri()
        properties = self.swis.read(uri)
        logger.debug(f"{self.ip}: details(): got existing properties")
        custom_properties = self.swis.read(f"{uri}/CustomProperties")
        logger.debug(f"{self.ip}: details(): got existing custom properties")
        return {
            "properties": properties,
            "custom_properties": custom_properties,
        }

    def diff(self):
        if self.exists():
            diff = {"properties": {}, "custom_properties": {}}
            if self.hostname:
                self.properties["Caption"] = self.hostname
            if self.properties is not None or self.custom_properties is not None:
                details = self.details()
                if self.properties is not None:
                    for k, v in self.properties.items():
                        if details["properties"][k] != v:
                            diff["properties"][k] = v
                if self.custom_properties is not None:
                    for k, v in self.custom_properties.items():
                        if details["custom_properties"][k] != v:
                            diff["custom_properties"][k] = v
            if diff["properties"] or diff["custom_properties"]:
                logger.debug(f"{self.ip}: diff(): found differences: {diff}")
                return diff
            else:
                logger.debug(f"{self.ip}: diff(): no differences found")
                return None

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

    def exists(self, force=False):
        if self.uri and force is False:
            logger.debug(
                f"{self.ip}: exists(): uri cached and no refresh forced, node exists"
            )
            return True
        else:
            try:
                self.get_uri(force=True)
                logger.debug(f"{self.ip}: exists(): uri found, node exists")
                return True
            except SWObjectNotFound:
                logger.debug(f"{self.ip}: exists(): uri not found, node does not exist")
                return False

    def get_uri(self, force=False):
        if (not self.uri) or (self.uri and force):
            logger.debug(
                f"{self.ip}: get_uri(): uri not cached (or refresh forced), querying api..."
            )
            if self.ip is not None:
                query = (
                    f"SELECT Uri AS uri FROM Orion.Nodes WHERE IPAddress = '{self.ip}'"
                )
                results = self.swis.query(query)["results"]
                if not results:
                    if self.hostname is not None:
                        logger.debug(
                            f"Node with IP address {self.ip} not found, trying hostname"
                        )
                        query = f"SELECT Uri AS uri FROM Orion.Nodes WHERE Caption = '{self.hostname}'"
                        results = self.swis.query(query)["results"]
                        if not results:
                            msg = f"Node with hostname {self.hostname} not found, giving up"
                            raise SWObjectNotFound(msg)
                    else:
                        raise SWObjectNotFound(
                            f"Node with IP address {self.ip} not found "
                            "and no hostname given, nothing else to try"
                        )

            if len(results) > 1:
                msg = f"Found more than 1 node. Check Solarwinds for duplicate. SWQL query: {query}"
                raise SWNonUniqueResult(msg)
            else:
                self.uri = results[0]["uri"]
                self.id = self.get_id()
                logger.debug(f"{self.ip}: get_uri(): got uri: {self.uri}")
        return self.uri

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
