import datetime
from typing import Dict, Optional

from pysolarwinds.endpoints import NewEndpoint
from pysolarwinds.utils import parse_datetime


class Engine(NewEndpoint):
    _entity_type = "Orion.Engines"
    _uri_template = "swis://{}/Orion/Orion.Engines/EngineID={}"

    @property
    def avg_cpu_used(self) -> float:
        """Average CPU utilization, most likely percentage."""
        return self.data["AvgCPUUtil"]

    @property
    def business_layer_port(self) -> int:
        """Port used for API data transfer."""
        return self.data["BusinessLayerPort"]

    @property
    def company_name(self) -> str:
        """Company name."""
        return self.data.get("CompanyName", "")

    @property
    def display_name(self) -> str:
        """Display name."""
        return self.data.get("DisplayName", "")

    @property
    def elements(self) -> int:
        return self.data["Elements"]

    @property
    def engine_version(self) -> str:
        return self.data["EngineVersion"]

    @property
    def eval_days_left(self) -> int:
        return self.data["EvalDaysLeft"]

    @property
    def evaluation(self) -> bool:
        return bool(self.data.get("Evaluation"))

    @property
    def fips_mode_enabled(self) -> bool:
        return bool(self.data["FIPSModeEnabled"])

    @property
    def failover_active(self) -> bool:
        return bool(self.data["FailOverActive"])

    @property
    def instance_site_id(self) -> int:
        return self.data["InstanceSiteId"]

    @property
    def interface_poll_interval(self) -> int:
        return self.data["InterfacePollInterval"]

    @property
    def interface_stat_poll_interval(self) -> int:
        return self.data["InterfaceStatPollInterval"]

    @property
    def interface_count(self) -> int:
        return self.data["Interfaces"]

    @property
    def ip_address(self) -> str:
        """IP address."""
        return self.data["IP"]

    @property
    def is_free(self) -> bool:
        return self.data["IsFree"]

    @property
    def keepalive(self) -> Optional[datetime.datetime]:
        return parse_datetime(self.data.get("KeepAlive"))

    @property
    def license_key(self) -> str:
        return self.data.get("LicenseKey", "")

    @property
    def licensed_element_count(self) -> int:
        return self.data["LicensedElements"]

    @property
    def master_engine_id(self) -> Optional[int]:
        return self.data.get("MasterEngineID")

    @property
    def max_polls_per_second(self) -> int:
        return self.data["MaxPollsPerSecond"]

    @property
    def max_stat_polls_per_second(self) -> int:
        return self.data["MaxStatPollsPerSecond"]

    @property
    def memory_used(self) -> float:
        return self.data["MemoryUtil"]

    @property
    def minutes_since_failover_active(self) -> Optional[int]:
        return self.data.get("MinutesSinceFailOverActive")

    @property
    def minutes_since_keepalive(self) -> Optional[int]:
        return self.data.get("MinutesSinceKeepAlive")

    @property
    def minutes_since_restart(self) -> Optional[int]:
        return self.data.get("MinutesSinceRestart")

    @property
    def minutes_since_start_time(self) -> Optional[int]:
        return self.data.get("MinutesSinceStartTime")

    @property
    def minutes_since_syslog_keepalive(self) -> Optional[int]:
        return self.data.get("MinutesSinceSysLogKeepAlive")

    @property
    def minutes_since_trap_keepalive(self) -> Optional[int]:
        return self.data.get("MinutesSinceTrapsKeepAlive")

    @property
    def name(self) -> str:
        """Object's name."""
        return self.display_name

    @property
    def node_poll_interval(self) -> int:
        return self.data["NodePollInterval"]

    @property
    def node_stat_poll_interval(self) -> int:
        return self.data["NodeStatPollInterval"]

    @property
    def node_count(self) -> int:
        return self.data["Nodes"]

    @property
    def package_name(self) -> str:
        return self.data.get("PackageName", "")

    @property
    def poller_count(self) -> int:
        return self.data["Pollers"]

    @property
    def polling_completion_percent(self) -> float:
        return self.data["PollingCompletion"]

    @property
    def primary_servers(self) -> Optional[str]:
        return self.data.get("PrimaryServers")

    @property
    def restart_datetime(self) -> Optional[datetime.datetime]:
        return parse_datetime(self.data["Restart"])

    @property
    def serial_number(self) -> Optional[str]:
        return self.data.get("SerialNumber")

    @property
    def server_name(self) -> Optional[str]:
        return self.data.get("ServerName")

    @property
    def server_type(self) -> str:
        return self.data.get("ServicePack", "")

    @property
    def start_time(self) -> Optional[datetime.datetime]:
        return parse_datetime(self.data.get("StartTime"))

    @property
    def stat_poll_interval(self) -> Optional[int]:
        return self.data.get("StatPollInterval")

    @property
    def syslog_keepalive(self) -> Optional[datetime.datetime]:
        return parse_datetime(self.data.get("SysLogKeepAlive"))

    @property
    def traps_keepalive(self) -> Optional[datetime.datetime]:
        return parse_datetime(self.data.get("TrapsKeepAlive"))

    @property
    def volume_poll_interval(self) -> Optional[int]:
        return self.data.get("VolumePollInterval")

    @property
    def volume_stat_poll_interval(self) -> int:
        return self.data["VolumeStatPollInterval"]

    @property
    def volume_count(self) -> int:
        return self.data["Volumes"]

    @property
    def windows_version(self) -> str:
        return self.data["WindowsVersion"]

    def __repr__(self):
        return f"Engine(id={self.id})"
