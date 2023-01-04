import re
from typing import Dict, Union

from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.engines import OrionEngine
from solarwinds.exceptions import (
    SWDiscoveryError,
    SWObjectDoesNotExist,
    SWObjectPropertyError,
)
from solarwinds.logging import get_logger

logger = get_logger(__name__)


class OrionInterface(Endpoint):
    endpoint = "Orion.NPM.Interfaces"
    _type = "interface"

    def __init__(self, node, data: Dict) -> None:
        self.node = node
        self.api = node.api
        self.data = data
        self.uri = data.get("uri")
        self._id = None
        self._name = None
        self._mtu = None
        self._mac_address = None
        self._duplex = None
        self._oper_status = None
        self._admin_status = None
        self._speed = None
        for k, v in data.items():
            setattr(self, f"_{k}", v)

    @property
    def id(self) -> int:
        return int(self._id)

    @property
    def name(self) -> str:
        return self._name.strip()

    @property
    def mtu(self) -> int:
        return int(self.mtu)

    @property
    def mac_address(self) -> str:
        return self._mac_address

    @property
    def duplex(self) -> str:
        return self._duplex

    @property
    def enabled(self) -> bool:
        return self._admin_status == 1

    @property
    def disabled(self) -> bool:
        return self.enabled is False

    @property
    def up(self) -> bool:
        return self._oper_status == 1

    @property
    def down(self) -> bool:
        return self.up is False

    @property
    def speed(self) -> int:
        return int(self._speed)

    def __repr__(self) -> str:
        return self.name


class OrionInterfaces(object):
    endpoint = "Orion.NPM.Interfaces"

    def __init__(self, node) -> None:
        self.node = node
        self.api = node.api
        self._existing = []
        self._discovered = []
        self._discovery_response_code = None

    def _get_iface_by_abbr(self, abbr):
        abbr = abbr.lower()
        abbr_pattern = r"^([a-z\-]+)([\d\/\:]+)$"
        match = re.match(abbr_pattern, abbr)
        if match:
            begin = match.group(1)
            end = match.group(2)
            full_pattern = re.compile(f"^{begin}[a-z\-]+{end}$", re.I)
            matches = []
            for iface in self._existing:
                if re.match(full_pattern, iface.name):
                    matches.append(iface)
            if len(matches) == 0:
                raise IndexError(f"no matches found: {abbr}")
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise IndexError(f"ambiguous reference: {abbr}")
        else:
            raise IndexError

    def add(self, interfaces):
        logger.info(f"{self.node.name}: monitoring {len(interfaces)} interfaces...")
        return self.api.invoke(
            "Orion.NPM.Interfaces",
            "AddInterfacesOnNode",
            self.node.id,
            interfaces,
            "AddDefaultPollers",
        )

    def get(self) -> None:
        """
        Queries for interfaces that have already been discovered and assigned
        to node
        """
        logger.info(f"{self.node.name}: getting existing interfaces...")
        query = f"""
            SELECT
                I.Uri AS uri,
                I.AdminStatus AS admin_status,
                I.InterfaceID AS id,
                I.InterfaceName AS name,
                I.MTU AS mtu,
                I.OperStatus AS oper_status,
                I.PhysicalAddress AS mac_address,
                I.Speed AS speed
            FROM
                Orion.Nodes N
            JOIN
                Orion.NPM.Interfaces I ON N.NodeID = I.NodeID
            WHERE
                N.NodeID = '{self.node.id}'
        """
        result = self.api.query(query)
        if result:
            self._existing = [OrionInterface(self.node, data=data) for data in result]
        logger.info(
            f"{self.node.name}: found {len(self._existing)} existing interfaces"
        )

    def discover(self) -> bool:
        """
        Runs SNMP discovery of all available interfaces. This can take a while
        depending on network conditions and number of interfaces on node
        """
        if not self.node.exists():
            raise SWObjectDoesNotExist(
                f"{self.node}: node does not exist, can't discover interfaces"
            )
        if self.node.polling_method != "snmp":
            raise SWObjectPropertyError(
                f"{self.node}: interface discovery requires SNMP polling method; "
                f'node polling method is currently "{self.node.polling_method}"'
            )
        logger.info(f"{self.node.name}: discovering interfaces via SNMP...")

        # the verbs associated with this method need to be pointed at this
        # node's assigned polling engine. If they are directed at the main SWIS
        # server and the node uses a different polling engine, the process
        # will hang at "unknown" status
        if not isinstance(self.node.polling_engine, OrionEngine):
            self._resolve_endpoint_attrs()
        api_hostname = self.api.hostname
        self.api.hostname = self.node.polling_engine.ip_address
        result = self.api.invoke(
            "Orion.NPM.Interfaces", "DiscoverInterfacesOnNode", self.node.id
        )
        self.api.hostname = api_hostname
        self._discovery_response_code = result["Result"]
        if self._discovery_response_code == 0:
            results = result["DiscoveredInterfaces"]
            logger.info(f"{self.node.name}: discovered {len(results)} interfaces")
            self._discovered = results
            return True
        else:
            msg = f"{self.node}: Interface discovery failed. "
            # https://thwack.solarwinds.com/product-forums/the-orion-platform/f/orion-sdk/40430/data-returned-from-discoverinterfacesonnode-question/159593#159593
            if self._discovery_response_code == 1:
                # should never get this due to checks above
                msg += "Check that the node exists and is set to SNMP polling method."
            else:
                msg += (
                    "Common causes: Invalid SNMP credentials; "
                    "SNMP not running or misconfigured on node; "
                    "SNMP ports blocked by firewall or ACL"
                )
                raise SWDiscoveryError(msg)

    def monitor(self, interfaces=None) -> None:
        if not self._existing:
            self.get()

        if interfaces is None:
            self.discover()
            self.add(self._discovered)
        else:
            existing = [x.name for x in self._existing]
            missing = [x for x in interfaces if x not in existing]
            extraneous = [x for x in self._existing if x.name not in interfaces]

            if missing:
                logger.info(
                    f"{self.node.name}: found {len(missing)} missing interfaces"
                )
                self.discover()
                to_add = [
                    x
                    for x in self._discovered
                    if x["Caption"].split(" ")[0] in interfaces
                ]
                if to_add:
                    self.add(to_add)

            if extraneous:
                logger.info(
                    f"{self.node.name}: found {len(extraneous)} interfaces to delete"
                )
                for intf in extraneous:
                    intf.delete()

            if not missing and not extraneous:
                logger.info(
                    f"{self.node.name}: all {len(interfaces)} provided interfaces "
                    "already monitored, doing nothing"
                )

    def __getitem__(self, item: Union[str, int]) -> OrionInterface:
        if isinstance(item, int):
            return self._existing[item]
        else:
            try:
                result = [x for x in self._existing if x.name.lower() == item.lower()][
                    0
                ]
            except IndexError:
                result = self._get_iface_by_abbr(item)
            return result

    def __repr__(self) -> str:
        if self._existing is None:
            self.get()
        return str(self._existing)
