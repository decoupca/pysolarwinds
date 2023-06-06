import datetime
import re
from typing import Literal, Optional, Union

import netaddr

from pysolarwinds.endpoints import NewEndpoint
from pysolarwinds.endpoints.orion.engines import OrionEngine
from pysolarwinds.exceptions import (
    SWDiscoveryError,
    SWObjectNotFound,
    SWObjectPropertyError,
)
from pysolarwinds.logging import get_logger
from pysolarwinds.queries.orion.interfaces import QUERY, TABLE

logger = get_logger(__name__)


class OrionInterface(NewEndpoint):
    _entity_type = "Orion.NPM.Interfaces"
    _uri_template = "swis://{}/Orion/Orion.NPM.Interfaces/InterfaceID={}"

    def __init__(
        self,
        node: "OrionNode",
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        super().__init__(swis=node.swis, id=id, uri=uri, data=data)

    @property
    def _id(self) -> int:
        return int(self.data["InterfaceID"])

    @property
    def admin_status(self) -> int:
        """Administrative status."""
        return self.data["AdminStatus"]

    @property
    def admin_status_led(self) -> str:
        """Administrative status LED icon name."""
        return self.data["AdminStatusLED"].strip()

    @property
    def alias(self) -> str:
        """Interface alias."""
        return self.data["InterfaceAlias"]

    @property
    def allow_64bit_counters(self) -> bool:
        """Whether or not 64-bit SNMP counters are enabled."""
        return self.data["Counter64"] == "Y"

    @property
    def bps(self) -> float:
        """Unclear meaning."""
        return self.data["Bps"]

    @property
    def crc_align_errors_this_hour(self) -> float:
        """CRC align errors in the last 60 minutes."""
        return self.data["CRCAlignErrorsThisHour"]

    @property
    def crc_align_errors_today(self) -> float:
        """CRC align errors in the last 24 hours."""
        return self.data["CRCAlignErrorsToday"]

    @property
    def caption(self) -> str:
        """Abbreviate interface name."""
        return self.data["Caption"]

    @property
    def custom_bandwidth(self) -> bool:
        """Unknown meaning."""
        return self.data["CustomBandwidth"]

    @property
    def custom_poller_last_statistics_poll(self) -> datetime.datetime:
        last_poll = self.data["CustomPollerLastStatisticsPoll"]
        return datetime.datetime.strptime(last_poll, "%Y-%m-%dT%H:%M:%S")

    @property
    def description(self) -> str:
        """Interface description."""
        return self.data["InterfaceAlias"]  # This key is a misnomer

    @property
    def display_name(self) -> str:
        """Unabbreviated interface name."""
        return self.data["DisplayName"]

    @property
    def duplex_mode(self) -> int:
        """Duplex mode status code."""
        return self.data["DuplexMode"]

    @property
    def duplex(self) -> Optional[Literal["unknown", "half", "full"]]:
        """
        Human-friendly representation of duplex mode. Returns None when SolarWinds
        reports duplex mode is not applicable to this interface type.
        https://support.solarwinds.com/SuccessCenter/s/article/Duplex-mode-on-interfaces-in-NPM?language=en_US
        """
        return [None, "unknown", "half", "full"][self.duplex_mode]

    @property
    def full_name(self) -> str:
        """Node name with unabbreviated interface name and description."""
        return self.data["FullName"]

    @property
    def has_obsolete_data(self) -> bool:
        """Unknown meaning."""
        return bool(self.data["HasObsoleteData"])

    @property
    def icon(self) -> str:
        """Interface icon name."""
        return self.data["Icon"].strip()

    @property
    def ifname(self) -> str:
        """Abbreviated interface name."""
        return self.data["IfName"]

    @property
    def image(self) -> str:
        """Unknown meaning."""
        return self.data.get("Image", "")

    @property
    def input_bandwidth(self) -> float:
        """Inbound bandwidth in bits per second."""
        return self.data["InBandwidth"]

    @property
    def input_discards_this_hour(self) -> float:
        """Inbound discards in the last 60 minutes."""
        return self.data["InDiscardsThisHour"]

    @property
    def input_discards_today(self) -> float:
        """Inbound discards in the last 24 hours."""
        return self.data["InDiscardsThisHour"]

    @property
    def input_errors_this_hour(self) -> float:
        """Inbound errors in the last 60 minutes."""
        return self.data["InErrorsThisHour"]

    @property
    def input_errors_today(self) -> float:
        """Inbound errors in the last 24 hours."""
        return self.data["InErrorsThisHour"]

    @property
    def input_mcast_pps(self) -> float:
        """Inbound multicast packets per second."""
        return self.data["InMcastPps"]

    @property
    def input_percent_util(self) -> float:
        """Inbound bandwidth percent utilization."""
        return self.data["InPercentUtil"]

    @property
    def input_packet_size(self) -> int:
        """Presumably, average input packet size in bits."""
        return self.data["InPktSize"]

    @property
    def input_pps(self) -> float:
        """Inbound packets per second."""
        return self.data["InPps"]

    @property
    def input_ucast_pps(self) -> float:
        """Inbound unicast packets per second."""
        return self.data["InUcastPps"]

    @property
    def input_bps(self) -> float:
        """Inbound bits per second."""
        return self.data["Inbps"]

    @property
    def index(self) -> int:
        """Interface index (possibly SNMP index)."""
        return self.data["Index"]

    @property
    def is_responding(self) -> bool:
        """
        Whether or not the interface is responding.
        Unknown if this corresponds to an 'up/up' status.
        """
        return bool(self.data["InterfaceResponding"])

    @property
    def is_unmanaged(self) -> bool:
        """Whether or not interface is un-managed."""
        return self.data["UnManaged"]

    @property
    def is_unpluggable(self) -> bool:
        """Whether or not interface is un-pluggable."""
        return self.data["UnPluggable"]

    @property
    def last_change(self) -> datetime.datetime:
        """
        Last change to interface.
        Tests suggest this is the last configuration change, not status change.
        """
        last_change = self.data["LastChange"]
        return datetime.datetime.strptime(last_change, "%Y-%m-%dT%H:%M:%S.%f0")

    @property
    def last_sync(self) -> datetime.datetime:
        """Last sync with SolarWinds."""
        last_sync = self.data["LastSync"]
        return datetime.datetime.strptime(last_sync, "%Y-%m-%dT%H:%M:%S.%f0")

    @property
    def late_collisions_this_hour(self) -> float:
        """Late collisions in the last 60 minutes."""
        return self.data["LateCollisionsThisHour"]

    @property
    def late_collisions_today(self) -> float:
        """Late collisions in the last 24 hours."""
        return self.data["LateCollisionsToday"]

    @property
    def mac_address(self) -> Optional[netaddr.EUI]:
        if mac := self.data.get("PhysicalAddress"):
            return netaddr.EUI(mac)

    @property
    def max_input_bps_time(self) -> Optional[datetime.datetime]:
        """Date/time of max_input_bps_today."""
        if time := self.data.get("MaxInBpsTime"):
            return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f0")

    @property
    def max_input_bps_today(self) -> float:
        """Maximum input bps in the last 24 hours."""
        return self.data["MaxInBpsToday"]

    @property
    def max_output_bps_time(self) -> Optional[datetime.datetime]:
        """Date/time of max_output_bps_today."""
        if time := self.data.get("MaxOutBpsTime"):
            return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f0")

    @property
    def max_output_bps_today(self) -> float:
        """Maximum output bps in the last 24 hours."""
        return self.data["MaxOutBpsToday"]

    @property
    def minutes_since_last_sync(self) -> int:
        """Minutes since last sync with SolarWinds."""
        return self.data["MinutesSinceLastSync"]

    @property
    def mtu(self) -> int:
        return self.data["MTU"]

    @property
    def name(self) -> str:
        return self.data["Name"]

    @property
    def next_poll(self) -> datetime.datetime:
        """Next poll by SolarWinds."""
        next_poll = self.data["NextPoll"]
        return datetime.datetime.strftime(next_poll, "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def next_rediscovery(self) -> datetime.datetime:
        """Next rediscovery by SolarWinds."""
        next_rediscovery = self.data["NextPoll"]
        return datetime.datetime.strftime(next_rediscovery, "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def node_id(self) -> int:
        """Interface's parent node ID."""
        return self.data["NodeID"]

    @property
    def operational_status(self) -> int:
        """Operational status code."""
        return self.data["OperStatus"]

    @property
    def operational_status_led(self) -> str:
        """Operational status icon string."""
        return self.data["OperStatusLED"].strip()

    @property
    def output_bandwidth(self) -> float:
        """Outbound bandwidth in bits per second."""
        return self.data["OutBandwidth"]

    @property
    def output_discards_this_hour(self) -> float:
        """Outbound discards in the last 60 minutes."""
        return self.data["OutDiscardsThisHour"]

    @property
    def output_discards_today(self) -> float:
        """Outbound discards in the last 24 hours."""
        return self.data["OutDiscardsThisHour"]

    @property
    def output_errors_this_hour(self) -> float:
        """Outbound errors in the last 60 minutes."""
        return self.data["OutErrorsThisHour"]

    @property
    def output_errors_today(self) -> float:
        """Outbound errors in the last 24 hours."""
        return self.data["OutErrorsThisHour"]

    @property
    def output_mcast_pps(self) -> float:
        """Outbound multicast packets per second."""
        return self.data["OutMcastPps"]

    @property
    def output_percent_util(self) -> float:
        """Outbound bandwidth percent utilization."""
        return self.data["OutPercentUtil"]

    @property
    def output_packet_size(self) -> int:
        """Presumably, average output packet size in bits."""
        return self.data["OutPktSize"]

    @property
    def output_pps(self) -> float:
        """Outbound packets per second."""
        return self.data["OutPps"]

    @property
    def output_ucast_pps(self) -> float:
        """Outbound unicast packets per second."""
        return self.data["OutUcastPps"]

    @property
    def output_bps(self) -> float:
        """Outbound bits per second."""
        return self.data["Outbps"]

    @property
    def percent_util(self) -> float:
        """Percent utilization. Unknown how this maps to input/output usage."""
        return self.data["PercentUtil"]

    @property
    def type(self) -> str:
        """Interface type name."""
        return self.data["InterfaceTypeName"]

    @property
    def type_code(self) -> int:
        """Interface type code."""
        return self.data["InterfaceType"]

    @property
    def unmanage_from(self) -> Optional[datetime.datetime]:
        """Date/time to un-manage (if scheduled)."""
        if unmanage_from := self.data["UnManageFrom"]:
            return datetime.datetime.strptime(unmanage_from, "%Y-%m-%dT%H:%M:%S")

    @property
    def unmanage_until(self) -> Optional[datetime.datetime]:
        """Date/time to re-manage (if scheduled)."""
        if unmanage_until := self.data["UnManageUntil"]:
            return datetime.datetime.strptime(unmanage_until, "%Y-%m-%dT%H:%M:%S")

    def __repr__(self) -> str:
        return self.name


class OrionInterfaces(object):
    endpoint = "Orion.NPM.Interfaces"

    def __init__(self, node) -> None:
        self.node = node
        self.swis = node.swis
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
        return self.swis.invoke(
            "Orion.NPM.Interfaces",
            "AddInterfacesOnNode",
            self.node.id,
            interfaces,
            "AddDefaultPollers",
        )

    def fetch(self) -> None:
        """
        Queries for interfaces that have already been discovered and assigned
        to node
        """
        logger.info(f"Getting existing interfaces...")
        query = QUERY.where(TABLE.NodeID == self.node.id)
        if results := self.swis.query(query.get_sql()):
            self._existing = [OrionInterface(self.node, data=data) for data in results]
        logger.info(f"Found {len(self._existing)} existing interfaces.")

    def delete(self, interfaces: Union[OrionInterface, list[OrionInterface]]) -> bool:
        if isinstance(interfaces, OrionInterface):
            interfaces = [interfaces]

        uris = [x.uri for x in interfaces]
        self.swis.delete(uris)
        for interface in interfaces:
            if interface in self._existing:
                self._existing.remove(interface)
        logger.info(f"deleted {len(interfaces)} interfaces")
        return True

    def delete_all(self) -> bool:
        interface_count = len(self._existing)
        self.swis.delete([x.uri for x in self._existing])
        self._existing = []
        logger.info(f"{self.node}: deleted {interface_count} interfaces")
        return True

    def discover(self) -> bool:
        """
        Runs SNMP discovery of all available interfaces. This can take a while
        depending on network conditions and number of interfaces on node
        """
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
        swis_hostname = self.swis.hostname
        self.swis.hostname = self.node.polling_engine.ip_address
        result = self.swis.invoke(
            "Orion.NPM.Interfaces", "DiscoverInterfacesOnNode", self.node.id
        )
        self.swis.hostname = swis_hostname
        self._discovery_response_code = result["Result"]
        if self._discovery_response_code == 0:
            results = result["DiscoveredInterfaces"]
            if results:
                logger.info(f"{self.node.name}: discovered {len(results)} interfaces")
                self._discovered = results
                return True
            else:
                msg = (
                    f"{self.node}: No interfaces discovered. "
                    "The node may not have any interfaces available to monitor, "
                    "or there might be a problem with SNMP configuration / reachability. "
                    "The SWIS API is inconsistent in its response codes so precisely "
                    "identifying the cause isn't possible."
                )
                raise SWDiscoveryError(msg)
        else:
            msg = f"{self.node}: Interface discovery failed. "
            # https://thwack.pysolarwinds.com/product-forums/the-orion-platform/f/orion-sdk/40430/data-returned-from-discoverinterfacesonnode-question/159593#159593
            if self._discovery_response_code == 1:
                # should never get this due to checks above
                msg += "Check that the node exists and is set to SNMP polling method."
            else:
                msg += (
                    "Common causes: Invalid SNMP credentials; "
                    "SNMP misconfigured on node; "
                    "SNMP ports blocked by firewall or ACL"
                )
                raise SWDiscoveryError(msg)

    def monitor(
        self, interfaces: Optional[list[str]] = None, delete_extraneous: bool = False
    ) -> None:
        """
        Monitor interfaces on node.

        If interfaces is not provided, all discovered up interfaces will be monitored.
        If interfaces is provided, only interfaces matching the names of those provided
        will be monitored.
        If delete_extraneous is True, the provided interface list will be considered
        authoritative, and any interfaces currently monitored that are not in the provided
        list will be deleted.
        """
        if not self._existing:
            self.fetch()

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

            if delete_extraneous:
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

    def __len__(self) -> int:
        return len(self._existing)

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
