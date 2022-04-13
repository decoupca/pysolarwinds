from pysolarwinds.models import BaseModel
import re
from pysolarwinds.core.exceptions import (
    SWNonUniqueResultError,
    SWObjectExistsError,
    SWObjectNotFoundError,
    SWObjectPropertyError,
)

ICMP_POLLERS = [
    "N.Status.ICMP.Native",
    "N.ResponseTime.ICMP.Native",
]

SNMP_POLLERS = [
    "N.Status.SNMP.Native",
    "N.ResponseTime.SNMP.Native",
    "N.Details.SNMP.Generic",
    "N.Uptime.SNMP.Generic",
    "N.Cpu.SNMP.HrProcessorLoad",
    "N.Memory.SNMP.NetSnmpReal",
    "N.AssetInventory.Snmp.Generic",
    "N.Topology_Layer3.SNMP.ipNetToMedia",
    "N.Routing.SNMP.Ipv4CidrRoutingTable",
]


class Node(BaseModel):
    def _get_uri(self, ip=None, hostname=None):
        if hostname is None and ip is None:
            raise ValueError("Must provide hostname, IP, or both")
        where = []
        if hostname:
            where.append(f"Caption = '{hostname}'")
        if ip:
            where.append(f"IPAddress = '{ip}'")
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
            return results[0]["uri"]

    def create(
        self,
        ip=None,
        hostname=None,
        properties=None,
        custom_properties=None,
        pollers=None,
    ):

        # validate IP
        ip = ip or properties.get("IPAddress")
        if ip is None:
            raise SWObjectPropertyError(
                "Must provide polling IP as either ip argument, "
                "or IPAddress key in properties argument."
            )
        if self.exists(ip):
            raise SWObjectExistsError(f"Node with IP {ip} already exists.")

        # default props
        props = {
            "EngineID": 1,
            "ObjectSubType": "SNMP",
            "SNMPVersion": 2,
        }
        props.update({"IPAddress": ip})

        # update default props with provided values
        if properties:
            props.update(properties)

        # pollers
        if pollers is None:
            if props["ObjectSubType"] == "SNMP":
                pollers = SNMP_POLLERS
            else:
                pollers = ICMP_POLLERS

        # snmp
        if self.snmpv2c:
            community = self.snmpv2c.get("rw") or self.snmpv2c.get("ro")
            if community and props["ObjectSubType"] == "SNMP":
                props.update({"Community": community})

        # hostname
        hostname = hostname or properties.get("Caption")
        if hostname:
            props.update({"Caption": hostname})

        # create node
        uri = self.swis.create("Orion.Nodes", **props)

        # custom properties
        if custom_properties:
            self.update(uri=uri, custom_properties=custom_properties)

        # enable pollers
        if pollers:
            self.enable_pollers(uri=uri, pollers=pollers)

        return uri

    def delete(self, ip=None, hostname=None, uri=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        return self.swis.delete(uri)

    def details(self, ip=None, hostname=None, uri=None):
        if uri is None:
            uri = self._get_uri(ip=ip, hostname=hostname)
        return self.swis.read(uri)

    def enable_pollers(ip=None, hostname=None, pollers=None, uri=None):
        if uri is None:
            uri = self._get_uri(ip=ip, hostname=hostname)
        node_id = self.id(ip=ip, hostname=hostname, uri=uri)
        for poller_type in pollers:
            poller = {
                "PollerType": poller_type,
                "NetObject": f"N:{node_id}",
                "NetObjectType": "N",
                "NetObjectID": node_id,
                "Enabled": True,
            }
            swis.create("Orion.Pollers", **poller)

    def exists(self, ip=None, hostname=None):
        try:
            self._get_uri(ip=ip, hostname=hostname)
            return True
        except SWObjectNotFoundError:
            return False

    def id(self, ip=None, hostname=None, uri=None):
        if uri is None:
            uri = self._get_uri(ip=ip, hostname=hostname)
        return int(re.search(r"(\d+)$", uri).group(0))

    def update(
        self, ip=None, hostname=None, properties=None, custom_properties=None, uri=None
    ):
        if uri is None:
            uri = self._get_uri(ip=ip, hostname=hostname)
        if properties:
            if hostname:
                properties.update({"Caption": hostname})
            if ip:
                properties.update({"IPAddress": ip})
            self.swis.update(uri, **properties)
        if custom_properties:
            self.swis.update(f"{uri}/CustomProperties", **custom_properties)
