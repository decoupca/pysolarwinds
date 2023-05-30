from datetime import datetime
from typing import Dict, Optional

from pysolarwinds.swis import SWISClient
from pysolarwinds.endpoint import Endpoint
from pysolarwinds.utils import parse_datetime


class OrionEngine(Endpoint):
    endpoint = "Orion.Engines"
    _type = "engine"
    _id_attr = "id"
    _swid_key = "EngineID"
    _attr_map = {
        "id": "EngineID",
        "name": "ServerName",
        "ip_address": "IP",
    }
    _swquery_attrs = ["id", "name", "ip_address"]
    _swargs_attrs = ["id", "name", "ip_address"]

    def __init__(
        self,
        swis: SWISClient,
        id: Optional[int] = None,
        ip_address: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.swis = swis
        self.id = id
        self.ip_address = ip_address
        self.name = name
        super().__init__()

    def _get_attr_updates(self) -> Dict:
        swdata = self._swdata["properties"]
        return {
            "ip_address": swdata.get("IP"),
            "id": swdata.get("ID"),
            "name": swdata.get("ServerName"),
        }

    @property
    def avg_cpu_used_percent(self) -> Optional[float]:
        return self._swp.get("AvgCPUUtil")

    @property
    def business_layer_port(self) -> Optional[int]:
        return self._swp.get("BusinessLayerPort")

    @property
    def company_name(self) -> Optional[str]:
        return self._swp.get("CompanyName")

    @property
    def display_name(self) -> Optional[str]:
        return self._swp.get("DisplayName")

    @property
    def elements(self) -> Optional[int]:
        return self._swp.get("Elements")

    @property
    def engine_version(self) -> Optional[str]:
        return self._swp.get("EngineVersion")

    @property
    def eval_days_left(self) -> Optional[int]:
        return self._swp.get("EvalDaysLeft")

    @property
    def evaluation(self) -> bool:
        return bool(self._swp.get("Evaluation"))

    @property
    def fips_mode_enabled(self) -> bool:
        return bool(self._swp.get("FIPSModeEnabled"))

    @property
    def failover_active(self) -> bool:
        return bool(self._swp.get("FailOverActive"))

    @property
    def instance_site_id(self) -> Optional[int]:
        return self._swp.get("InstanceSiteId")

    @property
    def interface_poll_interval(self) -> Optional[int]:
        return self._swp.get("InterfacePollInterval")

    @property
    def interface_stat_poll_interval(self) -> Optional[int]:
        return self._swp.get("InterfaceStatPollInterval")

    @property
    def interface_count(self) -> Optional[int]:
        return self._swp.get("Interfaces")

    @property
    def is_free(self) -> bool:
        return bool(self._swp.get("IsFree"))

    @property
    def keepalive(self) -> Optional[str]:
        return self._swp.get("KeepAlive")

    @property
    def license_key(self) -> Optional[str]:
        return self._swp.get("LicenseKey")

    @property
    def licensed_element_count(self) -> Optional[int]:
        return self._swp.get("LicensedElements")

    @property
    def master_engine_id(self) -> Optional[int]:
        return self._swp.get("MasterEngineID")

    @property
    def max_polls_per_second(self) -> Optional[int]:
        return self._swp.get("MaxPollsPerSecond")

    @property
    def max_stat_polls_per_second(self) -> Optional[int]:
        return self._swp.get("MaxStatPollsPerSecond")

    @property
    def memory_used_percent(self) -> Optional[float]:
        return self._swp.get("MemoryUtil")

    @property
    def minutes_since_failover_active(self) -> Optional[int]:
        return self._swp.get("MinutesSinceFailOverActive")

    @property
    def minutes_since_keepalive(self) -> Optional[int]:
        return self._swp.get("MinutesSinceKeepAlive")

    @property
    def minutes_since_restart(self) -> Optional[int]:
        return self._swp.get("MinutesSinceRestart")

    @property
    def minutes_since_start_time(self) -> Optional[int]:
        return self._swp.get("MinutesSinceStartTime")

    @property
    def minutes_since_syslog_keepalive(self) -> Optional[int]:
        return self._swp.get("MinutesSinceSysLogKeepAlive")

    @property
    def minutes_since_trap_keepalive(self) -> Optional[int]:
        return self._swp.get("MinutesSinceTrapsKeepAlive")

    @property
    def node_poll_interval(self) -> Optional[int]:
        return self._swp.get("NodePollInterval")

    @property
    def node_stat_poll_interval(self) -> Optional[int]:
        return self._swp.get("NodeStatPollInterval")

    @property
    def node_count(self) -> Optional[int]:
        return self._swp.get("Nodes")

    @property
    def package_name(self) -> Optional[int]:
        return self._swp.get("PackageName")

    @property
    def poller_count(self) -> Optional[int]:
        return self._swp.get("Pollers")

    @property
    def polling_completion_percent(self) -> Optional[float]:
        return self._swp.get("PollingCompletion")

    @property
    def primary_servers(self) -> Optional[str]:
        return self._swp.get("PrimaryServers")

    @property
    def restart_datetime(self) -> Optional[datetime]:
        return parse_datetime(self._swp.get("Restart"))

    @property
    def serial_number(self) -> Optional[str]:
        return self._swp.get("SerialNumber")

    @property
    def server_name(self) -> Optional[str]:
        return self._swp.get("ServerName")

    @property
    def server_type(self) -> Optional[str]:
        return self._swp.get("ServicePack")

    @property
    def start_time(self) -> Optional[datetime]:
        return parse_datetime(self._swp.get("StartTime"))

    @property
    def stat_poll_interval(self) -> Optional[int]:
        return self._swp.get("StatPollInterval")

    @property
    def syslog_keepalive(self) -> Optional[datetime]:
        return parse_datetime(self._swp.get("SysLogKeepAlive"))

    @property
    def traps_keepalive(self) -> Optional[datetime]:
        return parse_datetime(self._swp.get("TrapsKeepAlive"))

    @property
    def volume_poll_interval(self) -> Optional[int]:
        return self._swp.get("VolumePollInterval")

    @property
    def volume_stat_poll_interval(self) -> Optional[int]:
        return self._swp.get("VolumeStatPollInterval")

    @property
    def volume_count(self) -> Optional[int]:
        return self._swp.get("Volumes")

    @property
    def windows_version(self) -> Optional[str]:
        return self._swp.get("WindowsVersion")

    def __repr__(self):
        return f"<OrionEngine: {self.name or self.ip_address or self.id}>"
