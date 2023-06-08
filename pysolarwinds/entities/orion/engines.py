"""SolarWinds polling engines."""
import datetime
from typing import Optional

import pytz

from pysolarwinds.entities import Entity


class Engine(Entity):
    """SolarWinds polling engines."""

    TYPE = "Orion.Engines"
    URI_TEMPLATE = "swis://{}/Orion/Orion.Engines/EngineID={}"

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
        """Number of monitored elements."""
        return self.data["Elements"]

    @property
    def engine_version(self) -> str:
        """Polling engine version."""
        return self.data["EngineVersion"]

    @property
    def eval_days_left(self) -> Optional[int]:
        """Number of days left in evaluation, if applicable."""
        return self.data.get("EvalDaysLeft")

    @property
    def fips_mode_enabled(self) -> bool:
        """Whether FIPS mode is enabled."""
        return bool(self.data["FIPSModeEnabled"])

    @property
    def failover_active(self) -> bool:
        """Whether failover is active."""
        return bool(self.data["FailOverActive"])

    @property
    def instance_site_id(self) -> int:
        """Unknown significance."""
        return self.data["InstanceSiteId"]

    @property
    def interface_poll_interval(self) -> int:
        """Interface polling interval (seconds)."""
        return self.data["InterfacePollInterval"]

    @property
    def interface_stat_poll_interval(self) -> int:
        """Interface statistics polling interval (seconds)."""
        return self.data["InterfaceStatPollInterval"]

    @property
    def interface_count(self) -> int:
        """Number of interfaces monitored on this poller."""
        return self.data["Interfaces"]

    @property
    def ip(self) -> str:
        """Convenience alias."""
        return self.ip_address

    @property
    def ip_address(self) -> str:
        """IP address."""
        return self.data["IP"]

    @property
    def is_evaluation(self) -> bool:
        """Whether engine is in evaluation mode."""
        return bool(self.data.get("Evaluation"))

    @property
    def is_free(self) -> bool:
        """Unknown significance."""
        return self.data["IsFree"]

    @property
    def keepalive(self) -> Optional[datetime.datetime]:
        """Unknown significance."""
        if keepalive := self.data.get("KeepAlive"):
            return datetime.datetime.strptime(
                keepalive, "%Y-%m-%dT%H:%M:%S.%f0"
            ).astimezone(tz=pytz.utc)
        return None

    @property
    def last_restart(self) -> Optional[datetime.datetime]:
        """Date/time of last restart."""
        if restart := self.data.get("Restart"):
            return datetime.datetime.strptime(
                restart, "%Y-%m-%dT%H:%M:%S.%f0"
            ).astimezone(tz=pytz.utc)
        return None

    @property
    def license_key(self) -> str:
        """Unknown significance."""
        return self.data.get("LicenseKey", "")

    @property
    def licensed_element_count(self) -> int:
        """Number of licensed elements on this polling engine."""
        return self.data["LicensedElements"]

    @property
    def master_engine_id(self) -> Optional[int]:
        """ID of master polling engine."""
        return self.data.get("MasterEngineID")

    @property
    def max_polls_per_second(self) -> int:
        """Maximum polls per second."""
        return self.data["MaxPollsPerSecond"]

    @property
    def max_stat_polls_per_second(self) -> int:
        """Maximim statistics polls per second."""
        return self.data["MaxStatPollsPerSecond"]

    @property
    def memory_used(self) -> float:
        """Memory utilization, likely in percentage."""
        return self.data["MemoryUtil"]

    @property
    def minutes_since_failover_active(self) -> Optional[int]:
        """Minute since failover."""
        return self.data.get("MinutesSinceFailOverActive")

    @property
    def minutes_since_keepalive(self) -> Optional[int]:
        """Minutes since keepalive."""
        return self.data.get("MinutesSinceKeepAlive")

    @property
    def minutes_since_restart(self) -> Optional[int]:
        """Minutes since restart."""
        return self.data.get("MinutesSinceRestart")

    @property
    def minutes_since_start_time(self) -> Optional[int]:
        """Minutes since start."""
        return self.data.get("MinutesSinceStartTime")

    @property
    def minutes_since_syslog_keepalive(self) -> Optional[int]:
        """Minutes since syslog keepalive."""
        return self.data.get("MinutesSinceSysLogKeepAlive")

    @property
    def minutes_since_trap_keepalive(self) -> Optional[int]:
        """Minutes since syslog keepalive."""
        return self.data.get("MinutesSinceTrapsKeepAlive")

    @property
    def name(self) -> str:
        """Polling engine name."""
        return self.display_name

    @property
    def node_poll_interval(self) -> int:
        """Node polling interval (seconds)."""
        return self.data["NodePollInterval"]

    @property
    def node_stat_poll_interval(self) -> int:
        """Node statistics polling interval (seconds)."""
        return self.data["NodeStatPollInterval"]

    @property
    def node_count(self) -> int:
        """Number of nodes managed by this polling engine."""
        return self.data["Nodes"]

    @property
    def package_name(self) -> str:
        """Unknown significance."""
        return self.data.get("PackageName", "")

    @property
    def poller_count(self) -> int:
        """Number of pollers managed by this polling engine."""
        return self.data["Pollers"]

    @property
    def polling_completion_percent(self) -> float:
        """Polling completion percent."""
        return self.data["PollingCompletion"]

    @property
    def primary_servers(self) -> Optional[str]:
        """Unknown significance."""
        return self.data.get("PrimaryServers")

    @property
    def serial_number(self) -> Optional[str]:
        """Serial number. Unknown source/meaning."""
        return self.data.get("SerialNumber")

    @property
    def server_name(self) -> Optional[str]:
        """Server hostname."""
        return self.data.get("ServerName")

    @property
    def service_pack(self) -> str:
        """(Presumably) Windows service pack level."""
        return self.data.get("ServicePack", "")

    @property
    def start_time(self) -> Optional[datetime.datetime]:
        """Date/time of last boot."""
        if start := self.data.get("StartTime"):
            return datetime.datetime.strptime(
                start, "%Y-%m-%dT%H:%M:%S.%f0"
            ).astimezone(tz=pytz.utc)
        return None

    @property
    def stat_poll_interval(self) -> Optional[int]:
        """Statistics polling interval."""
        return self.data.get("StatPollInterval")

    @property
    def syslog_keepalive(self) -> Optional[datetime.datetime]:
        """Date/time of last syslog keepalive."""
        if syslog := self.data.get("SysLogKeepAlive"):
            return datetime.datetime.strptime(
                syslog, "%Y-%m-%dT%H:%M:%S.%f0"
            ).astimezone(tz=pytz.utc)
        return None

    @property
    def traps_keepalive(self) -> Optional[datetime.datetime]:
        """Date/time of last traps keepalive."""
        if traps := self.data.get("TrapsKeepAlive"):
            return datetime.datetime.strptime(
                traps, "%Y-%m-%dT%H:%M:%S.%f0"
            ).astimezone(tz=pytz.utc)
        return None

    @property
    def volume_poll_interval(self) -> Optional[int]:
        """Volume polling interval (seconds)."""
        return self.data.get("VolumePollInterval")

    @property
    def volume_stat_poll_interval(self) -> int:
        """Volume statistics polling interval (seconds)."""
        return self.data["VolumeStatPollInterval"]

    @property
    def volume_count(self) -> int:
        """Number of volumes this polling engine monitors."""
        return self.data["Volumes"]

    @property
    def windows_version(self) -> str:
        """Windows version string."""
        return self.data["WindowsVersion"]

    def __repr__(self) -> str:
        return f"Engine(id={self.id})"
