import datetime
import re
import time
from typing import Callable, Literal, Optional, Union

import pytz

from pysolarwinds.custom_properties import CustomProperties
from pysolarwinds.entities import MonitoredEntity
from pysolarwinds.entities.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.entities.orion.engines import Engine
from pysolarwinds.entities.orion.interfaces import InterfaceList
from pysolarwinds.entities.orion.pollers import PollerList
from pysolarwinds.entities.orion.volumes import VolumeList
from pysolarwinds.exceptions import (
    SWAlertSuppressionError,
    SWNonUniqueResultError,
    SWObjectManageError,
    SWObjectNotFoundError,
    SWObjectPropertyError,
    SWResourceImportError,
)
from pysolarwinds.logging import get_logger
from pysolarwinds.maps import STATUS_MAP
from pysolarwinds.models.orion.node_settings import NodeSettings
from pysolarwinds.queries.orion.nodes import QUERY, TABLE
from pysolarwinds.swis import SWISClient

logger = get_logger(__name__)

ALERTS_ARE_SUPPRESSED = 1
ALERTS_WILL_BE_SUPPRESSED = 3


class Node(MonitoredEntity):
    TYPE = "Orion.Nodes"
    URI_TEMPLATE = "swis://{}/Orion/Orion.Nodes/NodeID={}"
    WRITE_ATTR_MAP = {
        "caption": "Caption",
        "ip_address": "IPAddress",
        "snmp_version": "SNMPVersion",
        "snmpv2_ro_community": "Community",
        "snmpv2_rw_community": "RWCommunity",
        "polling_method": "ObjectSubType",
    }

    def __init__(
        self,
        swis: SWISClient,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
        caption: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        super().__init__(
            swis=swis,
            data=data,
            uri=uri,
            id=id,
            caption=caption,
            ip_address=ip_address,
        )

        self._discovery_id = None
        self._discovery_batch_id = None
        self._discovery_status = None
        self._discovery_result = None
        self._discovered_items = None

        self._import_job_id = None
        self._import_status = None
        self._import_response = None

        self.caption: str = self.data.get("Caption", "") or caption
        self.custom_properties: CustomProperties = CustomProperties(
            swis=self.swis,
            entity=self,
        )
        self.interfaces: InterfaceList = InterfaceList(node=self)
        self.ip_address: str = self.data.get("IPAddress", "") or ip_address
        self.pollers: PollerList = PollerList(node=self)
        self.polling_engine: Engine = Engine(swis=swis, id=self.data["EngineID"])
        self.polling_method: str = self.data.get("ObjectSubType", "icmp").lower()
        self.settings: NodeSettings = NodeSettings(node=self)
        self.snmp_version: int = self.data.get("SNMPVersion", 0)
        self.snmpv2_ro_community: str = self.data.get("Community", "")
        self.snmpv2_rw_community: str = self.data.get("RWCommunity", "")
        self.snmpv3_ro_cred: Optional[SNMPv3Credential] = None
        self.snmpv3_rw_cred: Optional[SNMPv3Credential] = None
        self.volumes: VolumeList = VolumeList(node=self)

    @property
    def _id(self) -> int:
        """Retrieve entity ID from data dict."""
        return self.data["NodeID"]

    def _get_data(self) -> Optional[str]:
        """Try to retrieve data from caption or IP address."""
        if self.caption:
            query = QUERY.where(TABLE.Caption == self.caption)
            if result := self.swis.query(str(query)):
                if len(result) > 1:
                    msg = f'Found {len(result)} results with caption "{self.caption}".'
                    raise SWNonUniqueResultError(
                        msg,
                    )
                return result[0]
            else:
                msg = f'Node with caption "{self.caption}" not found.'
                raise SWObjectNotFoundError(msg)

        if self.ip_address:
            query = QUERY.where(TABLE.IPAddress == self.ip_address)
            if result := self.swis.query(str(query)):
                if len(result) > 1:
                    msg = f'Found {len(result)} results with ip_address "{self.ip_address}".'
                    raise SWNonUniqueResultError(
                        msg,
                    )
                return result[0]
            else:
                msg = f"Node with IP address {self.ip_address} not found."
                raise SWObjectNotFoundError(
                    msg,
                )
        return None

    @property
    def agent_port(self) -> Optional[int]:
        """Polling port."""
        return int(self.data.get("AgentPort")) if self.data.get("AgentPort") else None

    @property
    def allow_64bit_counters(self) -> bool:
        """Whether or not 64-bit counters are allowed."""
        return self.data["Allow64BitCounters"]

    @property
    def block_until(self) -> Optional[datetime.datetime]:
        """Unknown meaning."""
        block_until = self.data.get("BlockUntil")
        if block_until:
            return datetime.datetime.strptime(
                block_until, "%Y-%m-%dT%H:%M:%S"
            ).astimezone(tz=pytz.utc)
        return None

    @property
    def buffer_big_misses_this_hour(self) -> float:
        """Big buffer misses this hour."""
        return self.data["BufferBgMissThisHour"]

    @property
    def buffer_big_misses_today(self) -> float:
        """Big buffer misses today."""
        return self.data["BufferBgMissToday"]

    @property
    def buffer_huge_misses_this_hour(self) -> float:
        """Huge buffer misses this hour."""
        return self.data["BufferHgMissThisHour"]

    @property
    def buffer_huge_misses_today(self) -> float:
        """Huge buffer misses today."""
        return self.data["BufferHgMissToday"]

    @property
    def buffer_large_misses_this_hour(self) -> float:
        """Large buffer misses this hour."""
        return self.data["BufferLgMissThisHour"]

    @property
    def buffer_large_misses_today(self) -> float:
        """Large buffer misses today."""
        return self.data["BufferLgMissToday"]

    @property
    def buffer_medium_misses_this_hour(self) -> float:
        """Medium buffer misses today."""
        return self.data["BufferMdMissThisHour"]

    @property
    def buffer_medium_misses_today(self) -> float:
        """Medium buffer misses today."""
        return self.data["BufferMdMissToday"]

    @property
    def buffer_no_memory_this_hour(self) -> float:
        """Buffer no memory errors this hour."""
        return self.data["BufferNoMemThisHour"]

    @property
    def buffer_no_memory_today(self) -> float:
        """Buffer no memory errors today."""
        return self.data["BufferNoMemToday"]

    @property
    def buffer_small_misses_this_hour(self) -> float:
        """Small buffer misses this hour."""
        return self.data["BufferSmMissThisHour"]

    @property
    def buffer_small_misses_today(self) -> float:
        """Small buffer misses today."""
        return self.data["BufferSmMissToday"]

    @property
    def cpu_count(self) -> int:
        """Number of CPUs detected on node."""
        return self.data["CPUCount"]

    @property
    def cpu_load(self) -> int:
        """Integer representation of CPU load.

        This likely represents percentage, not load.
        """
        return self.data["CPULoad"]

    @property
    def category(self) -> int:
        """Category ID."""
        return self.data["Category"]

    @property
    def child_status(self) -> int:
        """Child status code."""
        return self.data["ChildStatus"]

    @property
    def contact(self) -> str:
        """SNMP contact."""
        return self.data["Contact"]

    @property
    def custom_status(self) -> bool:
        """Whether or not node has a custom status."""
        return self.data["CustomStatus"]

    @property
    def dns(self) -> str:
        """Node's FQDN."""
        return self.data.get("DNS", "")

    @property
    def dynamic_ip(self) -> bool:
        """Whether or not node uses a dynamic IP address."""
        return self.data["DynamicIP"]

    @property
    def ios_image(self) -> str:
        """Running network OS (not necessarily Cisco IOS)."""
        return self.data.get("IOSImage", "")

    @property
    def ip(self) -> str:
        """Convenience alias."""
        return self.ip_address

    @property
    def ip_address_type(self) -> str:
        """IP address family."""
        return self.data.get("IPAddressType", "")

    @property
    def is_cmts(self) -> bool:
        """Whether or not node is a CMTS."""
        return self.data["CMTS"] == "Y"

    @property
    def is_orion_server(self) -> bool:
        """Whether or not node is an Orion server."""
        return self.data["IsOrionServer"]

    @property
    def is_server(self) -> bool:
        """Whether or not node is a server."""
        return self.data["IsServer"]

    @property
    def last_boot(self) -> datetime.datetime:
        """Last boot date/time."""
        return datetime.datetime.strptime(
            self.data["LastBoot"], "%Y-%m-%dT%H:%M:%S"
        ).astimezone(tz=pytz.utc)

    @property
    def load_average_1(self) -> Optional[int]:
        """One-minute system load average."""
        return self.data["LoadAverage1"]

    @property
    def load_average_5(self) -> Optional[int]:
        """Five-minute system load average."""
        return self.data["LoadAverage5"]

    @property
    def load_averave_15(self) -> Optional[int]:
        """Fifteen-minute system load average."""
        return self.data["LoadAverage15"]

    @property
    def location(self) -> str:
        """SNMP location string."""
        return self.data["Location"]

    @property
    def machine_type(self) -> str:
        """Machine type string, typically hardware model."""
        return self.data["MachineType"]

    @property
    def memory_available(self) -> float:
        """Amount of memory available, most likely in bytes."""
        return self.data["MemoryAvailable"]

    @property
    def memory_used(self) -> float:
        """Amount of memory in use, most likely in bytes."""
        return self.data["MemoryUsed"]

    @property
    def name(self) -> str:
        """Object's name."""
        return self.caption

    @property
    def node_description(self) -> str:
        """Verbose node description."""
        return self.data["NodeDescription"]

    @property
    def percent_memory_available(self) -> int:
        """Percent memory available."""
        return self.data["PercentMemoryAvailable"]

    @property
    def percent_memory_used(self) -> int:
        """Percent memory used."""
        return self.data["PercentMemoryUsed"]

    @property
    def status_code(self) -> int:
        """Node status code."""
        return self.data["Status"]

    @property
    def status(self) -> str:
        """Node status."""
        return STATUS_MAP[self.status_code].lower()

    @property
    def sys_name(self) -> str:
        """SNMP system name."""
        return self.data["SysName"]

    @property
    def sys_object_id(self) -> str:
        """SNMP system OID."""
        return self.data["SysObjectID"]

    @property
    def uptime_sec(self) -> float:
        """System uptime in seconds."""
        return self.data["SystemUpTime"]

    @property
    def total_memory(self) -> float:
        """Total system memory, most likely in bytes."""
        return self.data["TotalMemory"]

    @property
    def uptime(self) -> datetime.timedelta:
        """Time since last boot."""
        return datetime.datetime.now(tz=pytz.utc) - self.last_boot

    @property
    def vendor(self) -> str:
        """System vendor."""
        return self.data["Vendor"]

    @property
    def alerts_are_suppressed(self) -> bool:
        """Whether or not alerts are currently suppressed on node."""
        return (
            self._get_alert_suppression_state()["SuppressionMode"]
            == ALERTS_ARE_SUPPRESSED
        )

    @property
    def alerts_will_be_suppressed(self) -> bool:
        """Whether or not alerts are scheduled to be suppressed at a future
        date/time.
        """
        return (
            self._get_alert_suppression_state()["SuppressionMode"]
            == ALERTS_WILL_BE_SUPPRESSED
        )

    @property
    def alerts_suppressed_from(self) -> Optional[datetime.datetime]:
        """Date/time from when alerts will be suppressed."""
        if suppressed_from := self._get_alert_suppression_state()["SuppressedFrom"]:
            return datetime.datetime.strptime(
                suppressed_from,
                "%Y-%m-%dT%H:%M:%S",
            ).astimezone(tz=pytz.utc)
        else:
            return None

    @property
    def alerts_suppressed_until(self) -> Optional[datetime.datetime]:
        """Date/time from when alerts will be resumed."""
        if suppressed_until := self._get_alert_suppression_state()["SuppressedUntil"]:
            return datetime.datetime.strptime(
                suppressed_until,
                "%Y-%m-%dT%H:%M:%S",
            ).astimezone(tz=pytz.utc)
        else:
            return None

    @property
    def alerts_are_muted(self) -> bool:
        """Convenience alias."""
        return self.alerts_are_suppressed

    @property
    def alerts_will_be_muted(self) -> bool:
        """Convenience alias."""
        return self.alerts_will_be_suppressed

    @property
    def alerts_muted_from(self) -> Optional[datetime.datetime]:
        """Convenience alias."""
        return self.alerts_suppressed_from

    @property
    def alerts_muted_until(self) -> Optional[datetime.datetime]:
        """Convenience alias."""
        return self.alerts_suppressed_until

    def _get_alert_suppression_state(self) -> dict:
        """Get raw alert suppression state on node."""
        return self.swis.invoke(
            "Orion.AlertSuppression",
            "GetAlertSuppressionState",
            [self.uri],
        )[0]

    def _get_import_status(self) -> None:
        """Get SNMP resource import status."""
        if not self._import_job_id:
            return
        self._import_status = self.swis.invoke(
            "Orion.Nodes",
            "GetScheduledListResourcesStatus",
            self._import_job_id,
            self.id,
        )

    def enforce_icmp_status_polling(self) -> None:
        """Ensures that node uses ICMP for up/down status and response time."""
        enable_pollers = [
            "N.Status.ICMP.Native",
            "N.ResponseTime.ICMP.Native",
        ]
        disable_pollers = [
            "N.Status.SNMP.Native",
            "N.ResponseTime.SNMP.Native",
        ]
        logger.info("Enforcing ICMP-based status and response time pollers...")
        self.pollers.fetch()
        for poller_name in enable_pollers:
            poller = self.pollers.get(poller_name)
            if poller:
                if not poller.is_enabled:
                    poller.enable()
            else:
                self.pollers.add(pollers=poller_name, enabled=True)

        for poller_name in disable_pollers:
            poller = self.pollers.get(poller_name)
            if poller and poller.is_enabled:
                poller.disable()

    def import_all_resources(self, timeout: float = 600.0) -> None:
        """Discovers, imports, and monitors all available SNMP resources.

        In most cases, this will leave the node in an undesirable state (i.e., with
        down interfaces). The more useful method is `import_resources`, which provides a
        means of removing undesired resources after import.

        Args:
            timeout: Maximum time in seconds to wait for SNMP resources to import. Generous timeouts
                are recommended in virtually all cases, because allowing pysolarwinds to time out will
                almost certainly leave the node in a state that will generate warnings or alerts due
                to down interfaces or full-capacity storage volumes. In most normal cases, imports
                take about 60-120 seconds. But high latency nodes with many OIDs can take upwards of
                5 minutes, hence the 10 minute (600s) default value.

        Returns:
            None.

        Raises:
            SWObjectPropertyError if polling_method is not 'snmp', or if no SNMP
                credentials were provided.
        """
        logger.info("Importing and monitoring all available SNMP resources...")
        if self.polling_method != "snmp":
            msg = "Polling_method must be 'snmp' to import resources."
            raise SWObjectPropertyError(msg)
        if (
            not self.snmpv2_ro_community
            and not self.snmpv2_rw_community
            and not self.snmpv3_ro_cred
            and not self.snmpv3_rw_cred
        ):
            msg = "Must set SNMPv2 community or SNMPv3 credentials."
            raise SWObjectPropertyError(msg)

        # The verbs associated with this method need to be pointed at this
        # node's assigned polling engine. If they are directed at the main SWIS
        # server and the node uses a different polling engine, the process
        # will hang at "unknown" status.
        swis_host = self.swis.host
        self.swis.host = self.polling_engine.ip_address
        self._import_job_id = self.swis.invoke(
            "Orion.Nodes", "ScheduleListResources", self.id
        )
        logger.debug(f"Resource import job ID: {self._import_job_id}")
        self._get_import_status()
        seconds_waited = 0
        report_increment = 5
        while seconds_waited < timeout and self._import_status != "ReadyForImport":
            time.sleep(report_increment)
            seconds_waited += report_increment
            self._get_import_status()
            logger.debug(
                f"Resource import: waited {seconds_waited}sec, "
                f"timeout {timeout}sec, status: {self._import_status}."
            )
        if self._import_status == "ReadyForImport":
            self._import_response = self.swis.invoke(
                "Orion.Nodes", "ImportListResourcesResult", self._import_job_id, self.id
            )
            if self._import_response:
                logger.info("Imported and monitored all SNMP resources.")
                self.swis.host = swis_host
                self.pollers.fetch()
            else:
                self.swis.host = swis_host
                msg = "SNMP resource import failed. SWIS does not provide any further info, sorry."
                raise SWResourceImportError(msg)
        else:
            self.swis.host = swis_host
            msg = f"Timed out waiting for SNMP resources ({timeout}sec)."
            raise SWResourceImportError(msg)

    def import_resources(  # noqa: C901, PLR0912, PLR0915
        self,
        *,
        enable_pollers: Union[None, list[str], Literal["all"]] = "all",
        purge_existing_pollers: bool,
        enforce_icmp_status_polling: bool,
        monitor_volumes: Union[
            None, list[str], Literal["existing", "all"], Callable
        ] = "existing",
        delete_volumes: Optional[Union[re.Pattern, list[re.Pattern]]] = None,
        monitor_interfaces: Union[
            None, list[str], Literal["existing", "up", "all"], Callable
        ] = "existing",
        delete_interfaces: Optional[Union[re.Pattern, list[re.Pattern]]] = None,
        unmanage_node: bool,
        unmanage_node_timeout: Union[datetime.timedelta, int] = datetime.timedelta(
            days=1
        ),
        remanage_delay: Optional[Union[datetime.timedelta, int]] = None,
        import_timeout: float = 600.0,
    ) -> None:
        """Imports and monitors SNMP resources.

        WARNING: Take care and test thoroughly if running against a node with *any* of these
        conditions, and *especially* nodes that meet more than one condition:
            - High-latency (300ms+ RTT)
            - Many interfaces (300+)
            - Uses a secondary polling engine (i.e., does not use the main SolarWinds server
              for polling)
        The ListResources verbs that import_resources use have produced unpredictable results
        when testing against nodes that meet any or all of the above conditions (see details
        below).

        SNMP resources include:
        1. SolarWinds pollers, which roughly correspond to system health OIDs such as CPU,
           RAM, routing tables, hardware health stats, etc. Available pollers vary by device
           type and platform version.
        2. Storage volumes, i.e. any persistent storage device that has a SNMP OID. Consider that
           some devices present system volumes that are not actually physical storage devices,
           but are rather loopback-mounted virtual devices, such as archives (JunOS). Since these
           are always at 100% storage capacity, monitoring them will trigger a warning condition.
           Consider using the monitor_volumes and/or delete_volumes options to filter them out.
        3. Interfaces. These include the usual physical and virtual interfaces you'd
           expect, as well as others you might not: stack ports, virtual application
           ports, or even more exotic stuff.

        monitor_resources works by invoking the ListResources verbs in SWIS, which imports
        all available resources from all three classes above. These verbs offer no granularity
        whatsoever--they don't even return a list of imported items. There is no way to select
        which resources, volumes, or interfaces you want--you can only import everything,
        then remove any pollers, volumes or interfaces you don't want after import.

        WARNING: The ListResources verbs are also dishonest under certain conditions, such as
                 heavy system load (as a result of, say, running many resource imports at the
                 same time). Under such conditions, ListResources verbs return successful
                 responses to invocations, but in fact, the import has failed. In such a case it
                 is impossible to tell if the verbs have succeeded or failed. This could leave
                 a node in a state that may generate alerts, or may not have system resources
                 monitored, without raising any exception. Testing suggests the best mitigation
                 is to limit concurrent invocations of ListResources to about 5-10 at a time. Further
                 testing suggests this condition also arises when running ListResources against
                 a high latency node with many interfaces, which is assigned a secondary polling
                 engine (i.e., not using the primary SolarWinds server for polling)

        Args:
            enable_pollers: Which pollers to enable. May be a list of poller names, or these values:
                all: enable all discovered pollers (default)
                None: disable all discovered pollers (i.e., delete all discovered pollers)
            purge_existing_pollers:
                Whether to delete all existing pollers before discovering/enabling all available pollers.
                Useful if existing pollers might be incorrect. Use
                caution when enabling this in a concurrent/threaded scenario; see warning above.
            monitor_interfaces: Which interfaces to monitor. May be a list of interface names,
                None, a callable object, or one of: 'existing', 'up', 'all'.
                existing (default): preserves existing interfaces (no net change to interfaces)
                up: Monitor all interfaces that SolarWinds reports as operationally and
                    administratively up
                all: Monitor all interfaces, regardless of their operational or
                    administrative status
                None: Do not monitor any interfaces (i.e., delete all imported interfaces)
                If a callable is provided, the interface will be provided as the only argument and
                the interface will be monitored if it returns a truthy response.
            monitor_volumes: Which volumes to monitor. May be a list of volume names, a callable
                object, or one of: 'existing', 'all':
                existing (default): preserves existing volumes (no net change)
                all: Monitor all available volumes
                None: Do not monitor any volumes (i.e., delete all imported volumes)
                If a callable is provided, the volume will be provided as the only argument and
                the volume will be monitored if it returns a truthy response.
            unmanange_node: Whether to unmanage (unmonitor) the node during
                the resource import process. The ListResources verbs import all available OIDs
                and interfaces, including any in a down or error state. Unmanaging the node before
                import may mitigate this. Be aware: for this to help, your alert definitions must
                account for node status. In other words, if your alert definition for interface
                down only considers the interface status, then unmanaging the node will have no
                protective effect on preventing false positive interface down alerts.
            unmanage_node_timeout: Maximum time to unmonitor the node for. May be a
                datetime.timedelta object, or an integer for seconds.
                The node will automatically re-manage itself after this timeout in case
                monitor_resources fails to automatically re-manage the node. In all intended
                cases, the node will be re-managed as soon as resource import has completed.
                This timeout is a failsafe to ensure that a node does not stay unmanaged
                indefinitely if the resource monitoring process fails before re-managing the node.
            remanage_delay: After successful resource import, delay re-managing node for this
                length of time. May be a datetime.timedelta object, or an integer for seconds. Defaults
                to None, i.e., after successful resource import, node will re-manage immediately.
                Delaying re-management may be helpful in corner cases, such as when importing resources
                for high-latency nodes with many interfaces polled by secondary polling engines. In
                testing, this combination of factors was shown to cause a condition where SWIS reported
                that down interfaces were deleted, but a propagation delay (or similar issue) caused
                the main SolarWinds engine to raise false positive alerts on those interfaces. Even though
                SWIS reported the interfaces were deleted, they existed in a transient state long
                enough to trigger down interface alerts. Delaying re-management of the node works around
                this by giving SolarWinds time to settle into its desired state before resuming alerts.
            import_timeout: Maximum time in seconds to wait for SNMP resources to import. Generous timeouts
                are recommended in virtually all cases, because allowing SolarWinds to time out will
                almost certainly leave the node in a state that will generate warnings or alerts due
                to down interfaces or full-capacity storage volumes. In most normal cases, imports
                take about 60-120 seconds. But high latency nodes with many OIDs can take upwards of
                5 minutes, hence the 10 minute (600s) default value.
            enforce_icmp_status_polling: SolarWinds recommends using ICMP to monitor status
                (up/down) and response time, which is faster than using SNMP. The ListResources
                verbs, however, automatically enable SNMP-based status and response time pollers.
                To override this and use the recommended ICMP-based status and response time pollers,
                set this to True.
            delete_interfaces: Regex pattern, or list of patterns. If any interface name matches
                any pattern, it will be excluded from monitoring (deleted after import).
            delete_volumes: Regex pattern, or list of patterns. If any volume name matches
                any pattern, it will be excluded from monitoring (deleted after import).

        Returns:
            None

        Raises:
            ValueError if node is unmanaged and interfaces == 'up'. When nodes are unmanaged,
                the operational state of all interfaces become unmananged too.
        """
        existing_interface_names = []
        interfaces_to_delete = []
        volumes_to_delete = []

        if monitor_interfaces == "up" and unmanage_node:
            msg = "Can't monitor up interfaces when node is unmanaged."
            raise ValueError(msg)

        already_unmanaged = self.is_unmanaged
        if monitor_interfaces == "up" and already_unmanaged:
            msg = "Can't monitor up interfaces when node is unmanaged."
            raise ValueError(msg)

        if unmanage_node:
            if already_unmanaged:
                logger.info("Node is already unmanaged; leaving as-is.")
            else:
                logger.info("Unmanaging node...")
                if isinstance(unmanage_node_timeout, datetime.timedelta):
                    delta = unmanage_node_timeout
                elif isinstance(unmanage_node_timeout, int):
                    delta = datetime.timedelta(seconds=unmanage_node_timeout)
                else:
                    msg = (
                        f"Unexpected value for unmanage_node_timeout: {unmanage_node_timeout}. "
                        "Must be either a positive integer (seconds) or a `datetime.timedelta` object."
                    )
                    raise ValueError(msg)
                self.unmanage(end=(datetime.datetime.now(tz=pytz.utc) + delta))

        if monitor_interfaces == "existing":
            logger.info("Getting existing interfaces to preserve...")
            self.interfaces.fetch()
            existing_interface_names = [x.name for x in self.interfaces]
            logger.info(f"Found {len(existing_interface_names)} existing interfaces.")

        if monitor_volumes == "existing":
            logger.info("Getting existing volumes to preserve...")
            existing_volume_names = [x.name for x in self.volumes]
            logger.info(f"Found {len(existing_volume_names)} existing volumes.")

        if purge_existing_pollers:
            logger.info("Purging existing pollers...")
            self.pollers.delete_all()

        self.import_all_resources(timeout=import_timeout)

        logger.info("Getting imported pollers...")
        self.pollers.fetch()
        logger.info(f"Found {len(self.pollers)} imported pollers.")
        if enable_pollers == "all":
            pass  # All imported pollers are enabled by default.
        elif enable_pollers is None:
            self.pollers.disable_all()
        elif isinstance(enable_pollers, list):
            for poller in self.pollers:
                if poller.name in enable_pollers:
                    if not poller.is_enabled:
                        poller.enable()
                else:
                    poller.disable()
            for poller_name in enable_pollers:
                poller = self.pollers.get(poller_name)
                if not poller:
                    logger.warning(f"Poller {poller_name} does not exist.")
        else:
            msg = f'Unexpected value for pollers: {enable_pollers}. Must be a list of poller names, "all", or None.'
            raise ValueError(msg)

        logger.info("Getting imported interfaces...")
        self.interfaces.fetch()
        logger.info(f"Found {len(self.interfaces)} imported interfaces.")
        if monitor_interfaces == "existing":
            interfaces_to_delete = [
                x for x in self.interfaces if x.name not in existing_interface_names
            ]
        elif monitor_interfaces == "up":
            interfaces_to_delete = [x for x in self.interfaces if not x.up]
        elif monitor_interfaces == "all":
            interfaces_to_delete = []
        elif monitor_interfaces is None:
            interfaces_to_delete = list(self.interfaces)
        elif isinstance(monitor_interfaces, list):
            interfaces_to_delete = [
                x for x in self.interfaces if x.name not in monitor_interfaces
            ]
        elif callable(monitor_interfaces):
            interfaces_to_delete = [
                x for x in self.interfaces if not monitor_interfaces(x)
            ]
        else:
            msg = f'Unexpected value for monitor_interfaces: {monitor_interfaces}. Must be a list of interface names, a callable, or one of these values: "existing", "up", "all", or None.'
            raise ValueError(msg)
        if delete_interfaces:
            if isinstance(delete_interfaces, re.Pattern):
                delete_interfaces = [delete_interfaces]
            for interface in self.interfaces:
                for pattern in delete_interfaces:
                    if re.search(pattern, interface.name):
                        logger.debug(
                            f"Deleting interface {interface} because "
                            f'it matches exclusion pattern "{pattern}".'
                        )
                        interfaces_to_delete.append(interface)

        if interfaces_to_delete:
            interfaces_to_delete = list(set(interfaces_to_delete))
            logger.info(f"Deleting {len(interfaces_to_delete)} unwanted interfaces...")
            self.interfaces.delete(interfaces_to_delete)

        logger.info("Getting imported volumes...")
        self.volumes.fetch()
        if monitor_volumes == "existing":
            volumes_to_delete = [
                x for x in self.volumes if x.name not in existing_volume_names
            ]
        elif monitor_volumes == "all":
            volumes_to_delete = []
        elif monitor_volumes is None:
            volumes_to_delete = list(self.volumes)
        elif isinstance(monitor_volumes, list):
            volumes_to_delete = [
                x for x in self.volumes if x.name not in monitor_volumes
            ]
        elif callable(monitor_volumes):
            volumes_to_delete = [x for x in self.volumes if not monitor_volumes(x)]
        else:
            msg = f'Unexpected value for monitor_volumes: {monitor_volumes}. Must be a list of volume names, a callable, or one of these values: "existing", "all", None.'
            raise ValueError(msg)
        if delete_volumes:
            if isinstance(delete_volumes, re.Pattern):
                delete_volumes = [delete_volumes]
            for volume in self.volumes:
                for pattern in delete_volumes:
                    if re.search(pattern, volume.name):
                        logger.debug(
                            f"Deleting volume {volume} because "
                            f'it matches exclusion pattern "{pattern}".'
                        )
                        volumes_to_delete.append(volume)
        if volumes_to_delete:
            logger.info(f"Deleting {len(volumes_to_delete)} unwanted volumes...")
            self.volumes.delete(volumes_to_delete)

        if unmanage_node and not already_unmanaged:
            if remanage_delay:
                if isinstance(remanage_delay, int):
                    delta = datetime.timedelta(seconds=remanage_delay)
                    msg = f"Setting node to re-manage in {remanage_delay}sec..."
                else:
                    delta = remanage_delay
                    msg = f"Delaying re-manage by {remanage_delay}..."
                logger.info(msg)
                self.unmanage(end=(datetime.utcnow() + delta))
            else:
                logger.info("Re-managing node...")
                self.remanage()

        if enforce_icmp_status_polling:
            self.enforce_icmp_status_polling()

        logger.info("Resource import complete.")

    def suppress_alerts(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
    ) -> None:
        """Suppress alerts on node.

        Any alerts that would normally be triggered by any condition(s) on the node,
        or its child objects (such as volumes or interfaces), will not be triggered.
        As soon as alerts are resumed, normal alerting behavior resumes.

        Args:
            start: `datetime.datetime` object (in UTC) for when to begin suppressing alerts.
                If omitted, suppression begins immediately.
            end: `datetime.datetime` object (in UTC) for when to resume normal alerting. If
                omitted, alerts will remain suppressed indefinitely.

        Returns:
            None.

        Raises:
            `SWAlertSuppressionError` if there was an unspecified problem suppressing alerts.
            Under normal conditions, invalid arguments will raise `SWISError` with details.
        """
        if start is None:
            start = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(hours=1)
        # If you provide datetime objects directly to this call, SWIS will
        # erroneously convert it to UTC, so we need to explicitly pass a datetime
        # string in this format: 2023-02-28T16:40:00Z. The trailing "Z" causes
        # SWIS to properly recognize the datetime is in UTC already, and makes
        # no erroneous conversion.
        self.swis.invoke(
            "Orion.AlertSuppression",
            "SuppressAlerts",
            [self.uri],
            datetime.datetime.strftime(start, "%Y-%m-%dT%H:%M:%SZ"),
            datetime.datetime.strftime(end, "%Y-%m-%dT%H:%M:%SZ") if end else None,
        )
        # The call above returns nothing on success or failure, so we need
        # to validate.
        suppression_state = self._get_alert_suppression_state()
        msg = (
            "Alert suppression failed, but SWIS didn't provide any error."
            "Check that start and end times are valid."
        )
        if not suppression_state["SuppressedFrom"]:
            raise SWAlertSuppressionError(msg)
        if end and not suppression_state["SuppressedUntil"]:
            raise SWAlertSuppressionError(msg)
        if end:
            msg = f"Suppressed alerts from {start} until {end}."
        else:
            msg = "Suppressed alerts indefinitely."
        logger.info(msg)

    def resume_alerts(self) -> None:
        """Resume alerts on node immediately.

        Also cancels planned alert suppression, if any.
        """
        # This call returns nothing if successful.
        self.swis.invoke("Orion.AlertSuppression", "ResumeAlerts", [self.uri])
        logger.info("Resumed alerts.")

    def mute_alerts(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
    ) -> None:
        """Convenience alias."""
        self.suppress_alerts(start=start, end=end)

    def unmute_alerts(self) -> None:
        """Convenience alias."""
        self.resume_alerts()

    def unmanage(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        duration: datetime.timedelta = datetime.timedelta(days=1),
    ) -> None:
        """Un-manages node with optional start and end times, or duration.

        Args:
            start: optional datetime object, in UTC, at which to start unmanaging the node.
                If not provided, defaults to now minus 10 minutes to account for small variances
                in clock synchronization between the local system and SolarWinds server. This provides
                greater assurance that a call to `unmanage` will have the expected effect of immediate
                un-management of the node.
            end: optional datetime object, in UTC, at which the node will automatically re-manage
                iteslf. If not provided, defaults to 1 day (86,400 seconds) from start.
            duration: timedelta object representing how long node should remain unmanaged. Defaults
                to 1 day (86,400 seconds).

        Returns:
            None.

        Raises:
            None.
        """
        now = datetime.datetime.now(tz=pytz.utc)
        if not start:
            start = now - datetime.timedelta(minutes=10)
        if not end:
            end = now + duration
        self.swis.invoke(
            "Orion.Nodes",
            "Unmanage",
            f"N:{self.id}",
            start,
            end,
            False,  # noqa: FBT003
        )
        logger.info(f"Un-managed node until {end}.")
        self.read()

    def remanage(self) -> None:
        """Re-manage node.

        Arguments:
            None.

        Returns:
            None.

        Raises:
            `SWObjectManageError` if node is already managed.
        """
        if self.is_unmanaged:
            self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
            logger.info("Re-managed node.")
            self.read()
        else:
            msg = "Node already managed, doing nothing."
            raise SWObjectManageError(msg)

    def save(self) -> None:
        updates = {
            "Caption": self.caption,
            "IPAddress": self.ip_address,
            "SNMPVersion": self.snmp_version,
            "Community": self.snmpv2_ro_community,
            "RWCommunity": self.snmpv2_rw_community,
            "ObjectSubType": self.polling_method.upper(),
        }
        super().save(updates=updates)
        self.settings.save()

    def __repr__(self) -> str:
        return f"Node(caption='{self.caption}')"
