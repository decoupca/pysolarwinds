import re
from copy import deepcopy

from solarwinds.core.exceptions import (
    SWNonUniqueResultError,
    SWObjectExistsError,
    SWObjectNotFoundError,
    SWObjectPropertyError,
)
from solarwinds.models import BaseModel

DEFAULT_PROPERTIES = {
    "EngineID": 1,
    "Status": 1,
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


class Node(BaseModel):
    def __init__(self, swis, **kwargs):
        super().__init__(swis)
        self.ip = kwargs.get("ip") or kwargs["properties"].get("IPAddress")
        if self.ip is None:
            raise SWObjectPropertyError(
                "Must provide polling IP as either ip argument, "
                "or IPAddress key in properties argument."
            )
        self.hostname = kwargs.get("hostname") or kwargs["properties"].get("Caption")
        self.id = None
        self.uri = None
        self.snmpv2c = kwargs.get("snmpv2c")
        self.properties = kwargs.get("properties")
        self.custom_properties = kwargs.get("custom_properties")

    def create(self):
        if self.exists():
            # TODO: implement overwrite/re-create option
            raise SWObjectExistsError(f"Node with IP {self.ip} already exists.")

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
                self.properties["ObjectSubtype"] = "SNMP"

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

        # create node
        self.uri = self.swis.create("Orion.Nodes", **self.properties)
        if self.custom_properties:
            self.update("custom_properties")
        if self.pollers:
            self.enable_pollers()
        return True

    def delete(self):
        self.swis.delete(self.get_uri())
        return True

    def details(self):
        return self.swis.read(self.get_uri())

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

    def exists(self):
        try:
            self.get_uri(force=True)
            return True
        except SWObjectNotFoundError:
            return False

    def get_uri(self, force=False):
        if (not self.uri) or (self.uri and force):
            if self.hostname is None and self.ip is None:
                raise ValueError("Must provide hostname, IP, or both")
            where = []
            if self.hostname:
                where.append(f"Caption = '{self.hostname}'")
            if self.ip:
                where.append(f"IPAddress = '{self.ip}'")
            where_clause = " AND ".join(where)
            query = f"SELECT Uri AS uri FROM Orion.Nodes WHERE {where_clause}"
            results = self.swis.query(query)["results"]
            if not results:
                msg = f"Node not found. Check hostname/IP. SWQL query: {query}"
                raise SWObjectNotFoundError(msg)
            if len(results) > 1:
                msg = (
                    f"Got {len(results)} results. Try a different combination of hostname/ip, "
                    f"or remove duplicates in Solarwinds.\nSWQL query: {query}"
                )
                raise SWNonUniqueResultError(msg)
            else:
                self.uri = results[0]["uri"]
                self.id = self.get_id()
        return self.uri

    def get_id(self):
        self.id = int(re.search(r"(\d+)$", self.get_uri()).group(0))
        return self.id

    def update(self, update="all"):
        uri = self.get_uri()
        if (update == "all" or update == "properties") and self.properties is not None:
            self.swis.update(uri, **self.properties)
        if (
            update == "all" or update == "custom_properties"
        ) and self.properties is not None:
            self.swis.update(f"{uri}/CustomProperties", **self.custom_properties)
        return True
