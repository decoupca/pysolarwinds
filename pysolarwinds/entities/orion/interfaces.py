import datetime
import re
from typing import Literal, Optional, Union

import netaddr

from pysolarwinds.entities import Entity
from pysolarwinds.exceptions import SWDiscoveryError, SWObjectPropertyError
from pysolarwinds.logging import get_logger
from pysolarwinds.maps import STATUS_MAP
from pysolarwinds.queries.orion.interfaces import QUERY, TABLE

logger = get_logger(__name__)


class Interface(Entity):
    TYPE = "Orion.NPM.Interfaces"
    URI_TEMPLATE = "swis://{}/Orion/Orion.Nodes/NodeID={}/Interfaces/InterfaceID={}"

    def __init__(
        self,
        node,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        super().__init__(swis=node.swis, id=id, uri=uri, data=data)

    @property
    def _id(self) -> int:
        return int(self.data["InterfaceID"])

    @property
    def admin_status(self) -> str:
        return STATUS_MAP[self.admin_status_code].lower()

    @property
    def admin_status_code(self) -> int:
        """Administrative status code."""
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
        if last_poll := self.data["CustomPollerLastStatisticsPoll"]:
            return datetime.datetime.strptime(last_poll, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

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
        """Human-friendly representation of duplex mode. Returns None when SolarWinds
        reports duplex mode is not applicable to this interface type.
        https://support.solarwinds.com/SuccessCenter/s/article/Duplex-mode-on-interfaces-in-NPM?language=en_US.
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
        """Whether or not the interface is responding.
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
    def last_change(self) -> Optional[datetime.datetime]:
        """Last change to interface.
        Tests suggest this is the last configuration change, not status change.
        """
        if last_change := self.data["LastChange"]:
            return datetime.datetime.strptime(last_change, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

    @property
    def last_sync(self) -> Optional[datetime.datetime]:
        """Last sync with SolarWinds."""
        if last_sync := self.data["LastSync"]:
            return datetime.datetime.strptime(last_sync, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

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
        return None

    @property
    def max_input_bps_time(self) -> Optional[datetime.datetime]:
        """Date/time of max_input_bps_today."""
        if time := self.data.get("MaxInBpsTime"):
            return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

    @property
    def max_input_bps_today(self) -> float:
        """Maximum input bps in the last 24 hours."""
        return self.data["MaxInBpsToday"]

    @property
    def max_output_bps_time(self) -> Optional[datetime.datetime]:
        """Date/time of max_output_bps_today."""
        if time := self.data.get("MaxOutBpsTime"):
            return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

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
    def next_poll(self) -> Optional[datetime.datetime]:
        """Next poll by SolarWinds."""
        if next_poll := self.data["NextPoll"]:
            return datetime.datetime.strptime(next_poll, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

    @property
    def next_rediscovery(self) -> datetime.datetime:
        """Next rediscovery by SolarWinds."""
        if next_rediscovery := self.data["NextPoll"]:
            return datetime.datetime.strptime(next_rediscovery, "%Y-%m-%dT%H:%M:%S.%f0")
        return None

    @property
    def node_id(self) -> int:
        """Interface's parent node ID."""
        return self.data["NodeID"]

    @property
    def oper_status(self) -> str:
        """Human-friendly operational status."""
        return STATUS_MAP[self.oper_status_code].lower()

    @property
    def oper_status_code(self) -> int:
        """Operational status code."""
        return self.data["OperStatus"]

    @property
    def oper_status_led(self) -> str:
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
    def status(self) -> str:
        """Convenience alias for oper_status."""
        return self.oper_status

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
        return None

    @property
    def unmanage_until(self) -> Optional[datetime.datetime]:
        """Date/time to re-manage (if scheduled)."""
        if unmanage_until := self.data["UnManageUntil"]:
            return datetime.datetime.strptime(unmanage_until, "%Y-%m-%dT%H:%M:%S")
        return None

    def __repr__(self) -> str:
        return self.name


class DiscoveredInterface:
    def __init__(self, data: dict) -> None:
        self.data: dict = data
        self.caption: str = data["Caption"]
        self.name: str = re.split(r"\s(\-|\·)\s", self.caption)[0]
        self.id: int = data["InterfaceID"]
        self.is_manageable: bool = data["Manageable"]
        self.admin_status: int = data["ifAdminStatus"]
        self.index: int = data["ifIndex"]
        self.oper_status: int = data["ifOperStatus"]
        self.speed: float = data["ifSpeed"]
        self.subtype: int = data["ifSubType"]
        self.type: int = data["ifType"]

    def __repr__(self) -> str:
        return f"DiscoveredInterface(name='{self.name}')"


class InterfaceList:
    def __init__(self, node) -> None:
        self.node = node
        self.swis = node.swis
        self._existing = []
        self._discovered = []
        self._discovery_response_code = None

    def _get_iface_by_abbr(self, abbr: str) -> Interface:
        abbr = abbr.lower()
        abbr_pattern = r"^([a-z\-]+)([\d\/\:]+)$"
        if match := re.match(abbr_pattern, abbr):
            begin = match.group(1)
            end = match.group(2)
            full_pattern = re.compile(f"^{begin}[a-z\\-]+{end}$", re.I)
            matches = []
            for iface in self._existing:
                if re.match(full_pattern, iface.name):
                    matches.append(iface)
            if len(matches) == 0:
                msg = f"No matches found: {abbr}"
                raise IndexError(msg)
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                msg = f"Ambiguous reference: {abbr}"
                raise IndexError(msg)
            return None
        else:
            raise IndexError

    def add(
        self, interfaces: Union[DiscoveredInterface, list[DiscoveredInterface]],
    ) -> None:
        """Adds one or more discovered interfaces to node, as a managed/monitored interface.

        Arguments:
            interfaces: A DiscoveredInterface, or list of DiscoveredInterface objects.

        Returns:
            None.

        Raises:
            None.

        """
        if isinstance(interfaces, DiscoveredInterface):
            interfaces = [interfaces]
        logger.info(f"Monitoring {len(interfaces)} interfaces...")
        self.swis.invoke(
            "Orion.NPM.Interfaces",
            "AddInterfacesOnNode",
            self.node.id,
            [x.data for x in interfaces],
            "AddDefaultPollers",
        )

    def fetch(self) -> None:
        """Retrieves interfaces that have already been discovered and monitored."""
        logger.info("Fetching existing interfaces...")
        query = QUERY.where(TABLE.NodeID == self.node.id)
        if results := self.swis.query(str(query)):
            self._existing = [Interface(node=self.node, data=data) for data in results]
        logger.info(f"Found {len(self._existing)} existing interfaces.")

    def delete(self, interfaces: Union[Interface, list[Interface]]) -> None:
        """Delete one or more currently monitored interfaces.

        Arguments:
            interfaces: An Interface object or list of Interface objects to delete.

        Returns:
            None.

        Raises:
            None.
        """
        if isinstance(interfaces, Interface):
            interfaces = [interfaces]
        self.swis.delete([x.uri for x in interfaces])
        for interface in interfaces:
            if interface in self._existing:
                self._existing.remove(interface)
        logger.info(f"Deleted {len(interfaces)} interfaces.")

    def delete_all(self) -> None:
        """Delete all currently discovered and monitored interfaces."""
        if self._existing:
            self.swis.delete([x.uri for x in self._existing])
            self._existing = []
            logger.info(f"Deleted all {len(self._existing)} interfaces.")
        else:
            logger.warning("No interfaces to delete.")

    def discover(self) -> None:
        """Discover all available interfaces via SNMP.

        Arguments:
            None.

        Returns:
            None.

        Raises:
            - SWObjectPropertyError if polling method is not 'snmp'.
            - SWDiscoveryError if there was a problem discovering interfaces.
        """
        if self.node.polling_method != "snmp":
            msg = f'Interface discovery requires SNMP polling method; node polling method is currently "{self.node.polling_method}".'
            raise SWObjectPropertyError(
                msg,
            )
        logger.info("Discovering interfaces via SNMP...")

        # The verbs associated with this method need to be pointed at this
        # node's assigned polling engine. If they are directed at the main SWIS
        # server and the node uses a different polling engine, the process
        # will hang at "unknown" status.
        swis_host = self.swis.host
        self.swis.host = self.node.polling_engine.ip_address
        result = self.swis.invoke(
            "Orion.NPM.Interfaces", "DiscoverInterfacesOnNode", self.node.id,
        )
        self.swis.host = swis_host
        self._discovery_response_code = result["Result"]
        if self._discovery_response_code == 0:
            if results := result["DiscoveredInterfaces"]:
                self._discovered = [
                    DiscoveredInterface(data=result) for result in results
                ]
                logger.info(f"Discovered {len(results)} interfaces.")
            else:
                msg = (
                    "No interfaces discovered. "
                    "The node may not have any interfaces available to monitor, "
                    "or there might be a problem with SNMP configuration / reachability. "
                    "The SWIS API is inconsistent in its response codes, so precisely "
                    "identifying the cause isn't currently possible."
                )
                raise SWDiscoveryError(msg)
        else:
            msg = "Interface discovery failed. "
            # https://thwack.pysolarwinds.com/product-forums/the-orion-platform/f/orion-sdk/40430/data-returned-from-discoverinterfacesonnode-question/159593#159593
            if self._discovery_response_code == 1:
                # Should never get this due to checks above.
                msg += "Check that the node exists and is set to SNMP polling method."
            else:
                msg += (
                    "Common causes: Invalid SNMP credentials; "
                    "SNMP misconfigured on node; "
                    "SNMP ports blocked by firewall or ACL."
                )
                raise SWDiscoveryError(msg)

    def monitor(
        self, interfaces: Optional[list[str]] = None, delete_extraneous: bool = False,
    ) -> None:
        """Monitor discovered interfaces on node.

        Arguments:
            interfaces: Optional list of interface names to monitor.
                If None, all discovered up/up interfaces will be monitored.
                If provided, only interfaces matching the names of those provided will be monitored.
            delete_extraneous: Whether or not to remove interfaces that are not in the list provided.
                If True, the provided interface list will be considered authoritative, and any interfaces
                currently monitored that are not in the provided list will be deleted.

        Returns:
            None.

        Raises:
            None.

        """
        if not self._existing:
            self.fetch()

        if interfaces is None:
            self.discover()
            self.add([x for x in self._discovered if x.oper_status == 1])
            self.fetch()
        else:
            existing = [x.name for x in self._existing]
            missing = [x for x in interfaces if x not in existing]
            extraneous = [x for x in self._existing if x.name not in interfaces]

            if missing:
                logger.info(f"Found {len(missing)} missing interfaces.")
                self.discover()
                to_add = [x.data for x in self._discovered if x.name in interfaces]
                if to_add:
                    self.add(to_add)

            if delete_extraneous and extraneous:
                logger.info(f"Found {len(extraneous)} interfaces to delete.")
                self.swis.delete([x.uri for x in extraneous])

            if not missing and not extraneous:
                logger.info(
                    f"All {len(interfaces)} provided interfaces already monitored; doing nothing.",
                )

    def __len__(self) -> int:
        return len(self._existing)

    def __getitem__(self, item: Union[str, int]) -> Interface:
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
        if not self._existing:
            self.fetch()
        return str(self._existing)
