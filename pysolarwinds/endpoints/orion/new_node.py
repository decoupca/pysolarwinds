import datetime
from typing import Optional

from pysolarwinds.endpoint import MonitoredEndpoint
from pysolarwinds.endpoints.orion.credential import OrionCredential
from pysolarwinds.endpoints.orion.engines import OrionEngine
from pysolarwinds.maps import NODE_STATUS_MAP
from pysolarwinds.swis import SWISClient


class OrionNode(MonitoredEndpoint):
    _entity_type = "Orion.Nodes"
    _uri_template = "swis://{}/Orion/Orion.Nodes/NodeID={}"
    _write_attr_map = {
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
        data: Optional[dict] = None,
        uri: Optional[str] = None,
        id: Optional[int] = None,
    ):
        super().__init__(swis=swis, data=data, uri=uri, id=id)
        self.caption: str = self.data.get("Caption", "")
        self.ip_address: str = self.data.get("IPAddress", "")
        # self.latitude = latitude
        # self.longitude = longitude
        self.polling_engine: OrionEngine = OrionEngine(
            swis=swis, id=self.data["EngineID"]
        )
        self.snmp_version: int = self.data.get("SNMPVersion", 0)
        self.snmpv2_ro_community: str = self.data.get("Community", "")
        self.snmpv2_rw_community: str = self.data.get("RWCommunity", "")
        # self.snmpv3_ro_cred = snmpv3_ro_cred
        # self.snmpv3_rw_cred = snmpv3_rw_cred
        self.polling_method: str = self.data.get("ObjectSubType", "").lower()

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
        """Integer representation of CPU load."""
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
        return NODE_STATUS_MAP[self.status_code]

    @property
    def sys_name(self) -> str:
        """SNMP system name."""
        return self.data["SysName"]

    @property
    def sys_object_id(self) -> str:
        """SNMP system OID."""
        return self.data["SysObjectID"]

    @property
    def system_uptime(self) -> float:
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
