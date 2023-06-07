import datetime
from typing import Optional

from pysolarwinds.entities import MonitoredEntity
from pysolarwinds.entities.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.entities.orion.engines import Engine
from pysolarwinds.entities.orion.interfaces import InterfaceList
from pysolarwinds.entities.orion.pollers import PollerList
from pysolarwinds.entities.orion.volumes import VolumeList
from pysolarwinds.entities.orion.worldmap import WorldMapPoint
from pysolarwinds.exceptions import (
    SWAlertSuppressionError,
    SWNonUniqueResultError,
    SWObjectManageError,
    SWObjectNotFound,
)
from pysolarwinds.logging import get_logger
from pysolarwinds.maps import STATUS_MAP
from pysolarwinds.models.orion.node_settings import NodeSettings
from pysolarwinds.swis import SWISClient

logger = get_logger(__name__)


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
    FIELDS = (
        "AgentPort",
        "Allow64BitCounters",
        "AncestorDetailsUrls",
        "AncestorDisplayNames",
        "AvgResponseTime",
        "BlockUntil",
        "BufferBgMissThisHour",
        "BufferBgMissToday",
        "BufferHgMissThisHour",
        "BufferHgMissToday",
        "BufferLgMissThisHour",
        "BufferLgMissToday",
        "BufferMdMissThisHour",
        "BufferMdMissToday",
        "BufferNoMemThisHour",
        "BufferNoMemToday",
        "BufferSmMissThisHour",
        "BufferSmMissToday",
        "CMTS",
        "CPUCount",
        "CPULoad",
        "Caption",
        "Category",
        "ChildStatus",
        "Community",
        "Contact",
        "CustomPollerLastStatisticsPoll",
        "CustomPollerLastStatisticsPollSuccess",
        "CustomStatus",
        "DNS",
        "Description",
        "DetailsUrl",
        "DisplayName",
        "DynamicIP",
        "EngineID",
        "EntityType",
        "External",
        "GroupStatus",
        "IOSImage",
        "IOSVersion",
        "IP",
        "IPAddress",
        "IPAddressGUID",
        "IPAddressType",
        "IP_Address",
        "Icon",
        "Image",
        "InstanceSiteId",
        "InstanceType",
        "IsOrionServer",
        "IsServer",
        "LastBoot",
        "LastSync",
        "LastSystemUpTimePollUtc",
        "LoadAverage1",
        "LoadAverage15",
        "LoadAverage5",
        "Location",
        "MachineType",
        "MaxResponseTime",
        "MemoryAvailable",
        "MemoryUsed",
        "MinResponseTime",
        "MinutesSinceLastSync",
        "NextPoll",
        "NextRediscovery",
        "NodeDescription",
        "NodeID",
        "NodeName",
        "NodeStatusRootCause",
        "NodeStatusRootCauseWithLinks",
        "ObjectSubType",
        "OrionIdColumn",
        "OrionIdPrefix",
        "PercentLoss",
        "PercentMemoryAvailable",
        "PercentMemoryUsed",
        "PollInterval",
        "PolledStatus",
        "RWCommunity",
        "RediscoveryInterval",
        "ResponseTime",
        "SNMPVersion",
        "Severity",
        "SkippedPollingCycles",
        "StatCollection",
        "Status",
        "StatusDescription",
        "StatusIcon",
        "StatusIconHint",
        "StatusLED",
        "SysName",
        "SysObjectID",
        "SystemUpTime",
        "TotalMemory",
        "UiSeverity",
        "UnManageFrom",
        "UnManageUntil",
        "UnManaged",
        "Uri",
        "Vendor",
        "VendorIcon",
    )

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
            swis=swis, data=data, uri=uri, id=id, caption=caption, ip_address=ip_address
        )

        self.caption: str = self.data.get("Caption", "") or caption
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

        # TODO: Custom properties

    @property
    def _id(self) -> int:
        """Retrieve entity ID from data dict."""
        return self.data["NodeID"]

    def _get_data(self) -> Optional[str]:
        """Try to retrieve data from caption or IP address."""
        if self.caption:
            query = self.QUERY.where(self.TABLE.Caption == self.caption)
            if result := self.swis.query(query.get_sql()):
                if len(result) > 1:
                    raise SWNonUniqueResultError(
                        f'Found {len(result)} results with caption "{self.caption}".'
                    )
                return result[0]
            else:
                raise SWObjectNotFound(f'Node with caption "{self.caption}" not found.')

        if self.ip_address:
            query = self.QUERY.where(self.TABLE.IPAddress == self.ip_address)
            if result := self.swis.query(query.get_sql()):
                if len(result) > 1:
                    raise SWNonUniqueResultError(
                        f'Found {len(result)} results with ip_address "{self.ip_address}".'
                    )
                return result[0]
            else:
                raise SWObjectNotFound(
                    f"Node with IP address {self.ip_address} not found."
                )

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
            return datetime.datetime.strptime(block_until, "%Y-%m-%dT%H:%M:%S")

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
        """Integer representation of CPU load. This likely represents percentage, not load."""
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
        return datetime.datetime.strptime(self.data["LastBoot"], "%Y-%m-%dT%H:%M:%S")

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
        return datetime.datetime.utcnow() - self.last_boot

    @property
    def vendor(self) -> str:
        """System vendor."""
        return self.data["Vendor"]

    def _get_alert_suppression_state(self) -> dict:
        """Get raw alert suppression state on node."""
        return self.swis.invoke(
            "Orion.AlertSuppression", "GetAlertSuppressionState", [self.uri]
        )[0]

    @property
    def alerts_are_suppressed(self) -> bool:
        """Whether or not alerts are currently suppressed on node."""
        return self._get_alert_suppression_state()["SuppressionMode"] == 1

    @property
    def alerts_will_be_suppressed(self) -> bool:
        """Whether or not alerts are scheduled to be suppressed at a future date/time."""
        return self._get_alert_suppression_state()["SuppressionMode"] == 3

    @property
    def alerts_suppressed_from(self) -> Optional[datetime.datetime]:
        """Date/time from when alerts will be suppressed."""
        if suppressed_from := self._get_alert_suppression_state()["SuppressedFrom"]:
            return datetime.datetime.strptime(suppressed_from, "%Y-%m-%dT%H:%M:%S")
        else:
            return None

    @property
    def alerts_suppressed_until(self) -> Optional[datetime.datetime]:
        """Date/time from when alerts will be resumed."""
        if suppressed_until := self._get_alert_suppression_state()["SuppressedUntil"]:
            return datetime.datetime.strptime(suppressed_until, "%Y-%m-%dT%H:%M:%S")
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
            if poller:
                if poller.is_enabled:
                    poller.disable()

    def suppress_alerts(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
    ) -> bool:
        """
        Suppress alerts on node.

        Any alerts that would normally be triggered by any condition(s) on the node,
        or its child objects (such as volumes or interfaces), will not be triggered.
        As soon as alerts are resumed, normal alerting behavior resumes.

        Args:
            start: `datetime.datetime` object (in UTC) for when to begin suppressing alerts.
                If omitted, suppression begins immediately.
            end: `datetime.datetime` object (in UTC) for when to resume normal alerting. If
                omitted, alerts will remain suppressed indefinitely.

        Returns: True if successful

        Raises:
            `SWAlertSuppressionError` if there was an unspecified problem suppressing alerts.
            Under normal conditions, invalid arguments will raise `SWISError` with details.
        """
        if start is None:
            start = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
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
            f"{self}: Alert suppression failed, but SWIS didn't provide any error."
            "Check that start and end times are valid."
        )
        if not suppression_state["SuppressedFrom"]:
            raise SWAlertSuppressionError(msg)
        if end:
            if not suppression_state["SuppressedUntil"]:
                raise SWAlertSuppressionError(msg)
        if end:
            msg = f"{self}: Suppressed alerts from {start} until {end}."
        else:
            msg = f"{self}: Suppressed alerts indefinitely."
        logger.info(msg)
        return True

    def resume_alerts(self) -> bool:
        """Resume alerts on node immediately. Also cancels planned alert suppression, if any."""
        # This call returns nothing if successful.
        self.swis.invoke("Orion.AlertSuppression", "ResumeAlerts", [self.uri])
        logger.info(f"{self}: Resumed alerts.")
        return True

    def mute_alerts(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
    ) -> bool:
        """Convenience alias"""
        return self.suppress_alerts(start=start, end=end)

    def unmute_alerts(self) -> bool:
        """Convenience alias"""
        return self.resume_alerts()

    def unmanage(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        duration: datetime.timedelta = datetime.timedelta(days=1),
    ) -> bool:
        """
        Un-manages node with optional start and end times, or duration.

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
        """
        now = datetime.datetime.utcnow()
        if not start:
            start = now - datetime.timedelta(minutes=10)
        if not end:
            end = now + duration
        self.swis.invoke("Orion.Nodes", "Unmanage", f"N:{self.id}", start, end, False)
        logger.info(f"Un-managed node until {end}.")
        self.read()
        return True

    def remanage(self) -> bool:
        """
        Re-manage node.

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
            return True
        else:
            raise SWObjectManageError("Node already managed, doing nothing.")

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
        if self.caption:
            return f"Node(caption='{self.caption}')"
        elif self.ip_address:
            return f"Node(ip_address='{self.ip_address}')"
        else:
            return f"Node(id={self.id})"
