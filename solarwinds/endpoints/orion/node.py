import re
from datetime import datetime, timedelta
from time import sleep
from typing import Dict, List, Literal, Optional, Union

import solarwinds.defaults as d
from solarwinds.api import API
from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.credential import OrionCredential, OrionSNMPv2Credential
from solarwinds.endpoints.orion.engines import OrionEngine
from solarwinds.endpoints.orion.interface import OrionInterfaces
from solarwinds.endpoints.orion.pollers import OrionPoller, OrionPollers
from solarwinds.endpoints.orion.volumes import OrionVolume, OrionVolumes
from solarwinds.endpoints.orion.worldmap import WorldMapPoint
from solarwinds.exceptions import (
    SWDiscoveryError,
    SWObjectPropertyError,
    SWResourceImportError,
)
from solarwinds.logging import get_logger
from solarwinds.maps import NODE_DISCOVERY_STATUS_MAP
from solarwinds.models.orion.node_settings import OrionNodeSettings

logger = get_logger(__name__)

DEFAULT_POLLING_ENGINE_ID = 1


class OrionNode(Endpoint):
    endpoint = "Orion.Nodes"
    _type = "node"
    _id_attr = "id"
    _swid_key = "NodeID"
    _swquery_attrs = ["ip_address", "caption"]
    _endpoint_attrs = {
        "polling_engine": OrionEngine,
    }
    _attr_map = {
        "caption": "Caption",
        "ip_address": "IPAddress",
        "snmp_version": "SNMPVersion",
        "snmpv2_ro_community": "Community",
        "snmpv2_rw_community": "RWCommunity",
    }
    _swargs_attrs = [
        "caption",
        "ip_address",
        "snmp_version",
        "snmpv2_ro_community",
        "snmpv2_rw_community",
    ]
    _required_swargs_attrs = ["ip_address", "polling_engine"]
    _child_objects = {
        "map_point": {
            "class": WorldMapPoint,
            "init_args": {
                "node_id": "instance_id",
            },
            "attr_map": {
                "node_id": "instance_id",
                "latitude": "latitude",
                "longitude": "longitude",
            },
        },
    }

    def __init__(
        self,
        api: API,
        ip_address: Optional[str] = None,
        caption: Optional[str] = None,
        custom_properties: Optional[Dict] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        id: Optional[int] = None,
        pollers: Optional[List[str]] = None,
        polling_engine: Union[OrionEngine, int, str, None] = None,
        polling_method: Optional[str] = None,
        snmp_version: Optional[int] = None,
        snmpv2_ro_community: Optional[str] = None,
        snmpv2_rw_community: Optional[str] = None,
        snmpv3_ro_cred: Optional[OrionCredential] = None,
        snmpv3_rw_cred: Optional[OrionCredential] = None,
    ):
        self.api = api
        self.caption = caption
        self.custom_properties = custom_properties
        self.ip_address = ip_address
        self.latitude = latitude
        self.longitude = longitude
        self.id = id
        self.polling_engine = polling_engine
        self.snmp_version = snmp_version
        self.snmpv2_ro_community = snmpv2_ro_community
        self.snmpv2_rw_community = snmpv2_rw_community
        self.snmpv3_ro_cred = snmpv3_ro_cred
        self.snmpv3_rw_cred = snmpv3_rw_cred
        self.polling_method = polling_method

        self.map_point = None

        self.settings = OrionNodeSettings(node=self)
        self.interfaces = OrionInterfaces(node=self)

        self._discovery_profile_id = None
        self._discovery_profile_status = 0
        self._discovered_entities = None

        self._import_job_id = None
        self._import_status = None

        if self.ip_address is None and self.caption is None:
            raise SWObjectPropertyError("Must provide either ip_address or caption")

        super().__init__()

        self.polling_method = self._get_polling_method()
        # if not self.exists():
        #     pollers = pollers or d.NODE_DEFAULT_POLLERS[self.polling_method]
        self.pollers = OrionPollers(node=self, enabled_pollers=pollers)
        self.volumes = OrionVolumes(node=self)

        if self.exists():
            self.settings.fetch()

    @property
    def name(self) -> Optional[str]:
        return self.caption

    @property
    def int(self) -> OrionInterfaces:
        return self.interfaces

    @property
    def ints(self) -> OrionInterfaces:
        return self.interfaces

    @property
    def intf(self) -> OrionInterfaces:
        return self.interfaces

    @property
    def intfs(self) -> OrionInterfaces:
        return self.interfaces

    @property
    def ip(self) -> Optional[str]:
        return self.ip_address

    @ip.setter
    def ip(self, ip_address: str) -> None:
        self.ip_address = ip_address

    @property
    def hostname(self) -> Optional[str]:
        return self.caption

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.caption = hostname

    @property
    def is_managed(self) -> Optional[bool]:
        if isinstance(self.status, int):
            return self.status != 9

    @property
    def status(self) -> Optional[str]:
        return self._swp.get("Status")

    @property
    def is_unmanaged(self) -> Optional[bool]:
        if isinstance(self.status, int):
            return self.status == 9

    def _set_defaults(self) -> None:
        if not self.polling_method:
            if self.snmpv2_ro_community or self.snmpv2_rw_community:
                self.polling_method = "snmp"
                self.snmp_version = 2
            elif self.snmpv3_ro_cred or self.snmpv3_rw_cred:
                self.polling_method = "snmp"
                self.snmp_version = 3
            else:
                self.polling_method = "icmp"
                self.snmp_version = 0

    def _get_attr_updates(self) -> Dict:
        """
        Get attribute updates from swdata
        """
        swdata = self._swdata["properties"]
        return {
            "caption": swdata["Caption"],
            "ip_address": swdata["IPAddress"],
            "snmpv2_ro_community": swdata["Community"],
            "snmpv2_rw_community": swdata["RWCommunity"],
            "polling_engine": OrionEngine(api=self.api, id=swdata["EngineID"]),
            "polling_method": self._get_polling_method(),
            "snmp_version": swdata["SNMPVersion"],
        }

    def _build_swargs(self) -> None:
        swargs = {"properties": None, "custom_properties": None}
        properties = {
            "Caption": self.caption,
            "IPAddress": self.ip_address,
            "Community": self.snmpv2_ro_community,
            "RWCommunity": self.snmpv2_rw_community,
            "ObjectSubType": self.polling_method,
            "SNMPVersion": self._get_snmp_version(),
            "EngineID": self.polling_engine.id,
        }
        custom_properties = {}

        extra_swargs = self._get_extra_swargs()
        if extra_swargs:
            for k, v in extra_swargs.items():
                properties[k] = v
                logger.debug(f'_swargs["properties"]["{k}"] = {v}')

        if hasattr(self, "custom_properties"):
            custom_properties = self.custom_properties
            logger.debug(f'_swargs["custom_properties"] = {self.custom_properties}')

        swargs["properties"] = properties
        swargs["custom_properties"] = custom_properties
        if swargs.get("properties") or swargs.get("custom_properties"):
            self._swargs = swargs

    def _get_discovery_status(self) -> None:
        if not self._discovery_profile_id:
            return None
        query = (
            "SELECT Status FROM Orion.DiscoveryProfiles "
            f"WHERE ProfileID = {self._discovery_profile_id}"
        )
        self._discovery_profile_status = self.api.query(query)[0]["Status"]

    def _get_import_status(self) -> None:
        if not self._import_job_id:
            return None
        self._import_status = self.api.invoke(
            "Orion.Nodes",
            "GetScheduledListResourcesStatus",
            self._import_job_id,
            self.id,
        )

    def _get_extra_swargs(self) -> Dict:
        extra_swargs = {
            "Status": self._swdata["properties"].get("Status") or 1,
            "ObjectSubType": self._get_polling_method().upper(),
        }
        return extra_swargs

    def _get_polling_method(self) -> str:
        """infer polling method from SNMP attributes if not explicitly given"""
        if not self.polling_method:
            ro_community = (
                self._swdata["properties"].get("Community") or self.snmpv2_ro_community
            )
            rw_community = (
                self._swdata["properties"].get("RWCommunity")
                or self.snmpv2_rw_community
            )
            if ro_community or rw_community or self.snmp_version != 0:
                return "snmp"
            else:
                return "icmp"
        else:
            return self.polling_method

    def _get_snmp_version(self) -> int:
        if self.snmpv2_ro_community or self.snmpv2_rw_community:
            return 2
        elif self.snmpv3_ro_cred or self.snmpv3_rw_cred:
            return 3
        else:
            return 0

    def create(self) -> bool:
        if not self.ip_address:
            raise SWObjectPropertyError(f"must provide IP address to create node")
        if not self.polling_engine:
            self.polling_engine = OrionEngine(
                api=self.api, id=DEFAULT_POLLING_ENGINE_ID
            )
        if isinstance(self.polling_engine, int):
            self.polling_engine = OrionEngine(api=self.api, id=self.polling_engine)
        if isinstance(self.polling_engine, str):
            self.polling_engine = OrionEngine(api=self.api, name=self.polling_engine)
        if not self.polling_engine.exists():
            raise SWObjectPropertyError(
                f"polling engine {self.polling_engine} does not exist"
            )
        # SWIS API won't let us create a SNMPv3 node directly,
        # so we need to first create it as a SNMPv2c node, then
        # switch it to SNMPv3
        snmp_version = self.snmp_version
        if snmp_version == 3:
            self.snmp_version = 2
        created = super().create()
        if created:
            if self.pollers._enabled_pollers:
                for poller in self.pollers._enabled_pollers:
                    self.pollers.add(poller=poller, enabled=True)
            if snmp_version == 3:
                self.snmp_version = 3
                self.save()
        return created

    def discover(self, retries=None, timeout=None, protocol="snmp") -> bool:
        if protocol != "snmp":
            raise NotImplementedError("Only SNMP-based discovery is implemented")
        if not self.ip_address:
            raise SWObjectPropertyError("Discovery requires ip_address is set")
        if (
            not self.snmpv2_ro_community
            and not self.snmpv2_rw_community
            and not self.snmpv3_ro_cred
            and not self.snmpv3_rw_cred
        ):
            raise SWObjectPropertyError(
                "Discovery requires at least one SNMP credential or community property set: "
                "snmpv2_ro_community, snmpv2_rw_community, snmpv3_ro_cred, or snmpv3_rw_cred"
            )
        if not self.polling_engine:
            self.polling_engine = OrionEngine(
                api=self.api, id=DEFAULT_POLLING_ENGINE_ID
            )
        if retries is None:
            retries = d.NODE_DISCOVERY_SNMP_RETRIES
        if timeout is None:
            timeout = d.NODE_DISCOVERY_JOB_TIMEOUT_SECONDS
        self._resolve_endpoint_attrs()

        credentials = []
        order = 1
        if self.snmp_version == 2:
            if self.snmpv2_rw_community:
                cred = OrionSNMPv2Credential(
                    api=self.api, name=self.snmpv2_rw_community
                )
                if cred.exists():
                    credentials.append({"CredentialID": cred.id, "Order": order})
                    order += 1
            if self.snmpv2_ro_community:
                cred = OrionSNMPv2Credential(
                    api=self.api, name=self.snmpv2_ro_community
                )
                if cred.exists():
                    credentials.append({"CredentialID": cred.id, "Order": order})
                    order += 1
        if self.snmp_version == 3:
            if self.snmpv3_rw_cred:
                credentials.append(
                    {
                        "CredentialID": self.snmpv3_rw_cred.id,
                        "Order": order,
                    }
                )
                order += 1
            if self.snmpv3_ro_cred:
                credentials.append(
                    {
                        "CredentialID": self.snmpv3_ro_cred.id,
                        "Order": order,
                    }
                )
        if not credentials:
            raise ValueError("No provided SNMP credentials are valid")

        core_plugin_context = {
            "BulkList": [{"Address": self.ip_address}],
            "Credentials": credentials,
            "WmiRetriesCount": 0,
            "WmiRetryIntervalMiliseconds": 1000,
        }
        core_plugin_config = self.api.invoke(
            "Orion.Discovery", "CreateCorePluginConfiguration", core_plugin_context
        )
        discovery_profile = {
            # N.B.: "milliseconds" is misspelled in keys below
            "Name": f"Discover {self.name}",
            "EngineId": self.polling_engine.id,
            "JobTimeoutSeconds": d.NODE_DISCOVERY_JOB_TIMEOUT_SECONDS,
            "SearchTimeoutMiliseconds": d.NODE_DISCOVERY_SEARCH_TIMEOUT_MILLISECONDS,
            "SnmpTimeoutMiliseconds": d.NODE_DISCOVERY_SNMP_TIMEOUT_MILLISECONDS,
            "SnmpRetries": retries,
            "RepeatIntervalMiliseconds": d.NODE_DISCOVERY_REPEAT_INTERVAL_MILLISECONDS,
            "SnmpPort": d.NODE_DISCOVERY_SNMP_PORT,
            "HopCount": d.NODE_DISCOVERY_HOP_COUNT,
            "PreferredSnmpVersion": d.NODE_DISCOVERY_PREFERRED_SNMP_VERSION,
            "DisableIcmp": d.NODE_DISCOVERY_DISABLE_ICMP,
            "AllowDuplicateNodes": d.NODE_DISCOVERY_ALLOW_DUPLICATE_NODES,
            "IsAutoImport": d.NODE_DISCOVERY_IS_AUTO_IMPORT,
            "IsHidden": d.NODE_DISCOVERY_IS_HIDDEN,
            "PluginConfigurations": [
                {"PluginConfigurationItem": core_plugin_config},
            ],
        }
        import ipdb

        ipdb.set_trace()
        self._discovery_profile_id = self.api.invoke(
            "Orion.Discovery", "StartDiscovery", discovery_profile
        )
        logger.info(
            f"{self.name}: discovering node: job id: {self._discovery_profile_id}..."
        )
        self._get_discovery_status()
        seconds_waited = 0
        report_increment = 5
        while seconds_waited < timeout and self._discovery_profile_status == 1:
            sleep(report_increment)
            seconds_waited += report_increment
            self._get_discovery_status()
            logger.debug(
                f"discovering node: waited {seconds_waited}sec, timeout {timeout}sec, "
                f"status: {NODE_DISCOVERY_STATUS_MAP[self._discovery_profile_status]}"
            )

        if self._discovery_profile_status == 2:
            query = (
                "SELECT Result, ResultDescription, ErrorMessage, BatchID "
                f"FROM Orion.DiscoveryLogs WHERE ProfileID = {self._discovery_profile_id}"
            )
            result = self.api.query(query)
            result_code = result[0]["Result"]
        else:
            raise SWDiscoveryError(
                f"{self.name}: node discovery failed. last status: {NODE_DISCOVERY_STATUS_MAP[self._discovery_profile_status]}"
            )

        if result_code == 2:
            logger.info(
                f"{self.name}: node discovery job finished, getting discovered items..."
            )
            batch_id = result[0]["BatchID"]
            query = (
                "SELECT EntityType, DisplayName, NetObjectID FROM "
                f"Orion.DiscoveryLogItems WHERE BatchID = '{batch_id}'"
            )
            self._discovered_entities = self.api.query(query)
            if self._discovered_entities:
                self._get_swdata()
                self.caption = self._swp.get("Caption")
                return True
            else:
                raise SWDiscoveryError(f"{self.name}: discovery found no items.")
        else:
            error_status = NODE_DISCOVERY_STATUS_MAP[result_code]
            error_message = result["ErrorMessage"]
            raise SWDiscoveryError(
                f"{self.name}: node discovery failed. Status: {error_status}, Error: {error_message}"
            )

    def import_snmp_resources(self, timeout=None) -> bool:
        """
        discovers and adds to monitoring all available SNMP OIDs,
        such as interfaces, CPU/RAM stats, routing tables, etc.
        AFAICT, the SWIS API provides no way of choosing which resources to import
        """
        logger.info(
            f"{self.name}: importing and monitoring all available SNMP resources (OIDs)..."
        )
        if self.polling_method != "snmp":
            raise SWObjectPropertyError(
                f"{self.name}: polling_method must be 'snmp' to import resources"
            )
        else:
            if (
                not self.snmpv2_ro_community
                and not self.snmpv2_rw_community
                and not self.snmpv3_ro_cred
                and not self.snmpv3_rw_cred
            ):
                raise SWObjectPropertyError(
                    f"{self.name}: must set SNMPv2 community or SNMPv3 credentials"
                )
        if timeout is None:
            timeout = d.IMPORT_RESOURCES_TIMEOUT

        # the verbs associated with this method need to be pointed at this
        # node's assigned polling engine. If they are directed at the main SWIS
        # server and the node uses a different polling engine, the process
        # will hang at "unknown" status
        if not isinstance(self.polling_engine, OrionEngine):
            self._resolve_endpoint_attrs()
        api_hostname = self.api.hostname
        self.api.hostname = self.polling_engine.ip_address

        self._import_job_id = self.api.invoke(
            "Orion.Nodes", "ScheduleListResources", self.id
        )
        logger.debug(f"{self.name}: resource import job ID: {self._import_job_id}")
        self._get_import_status()
        seconds_waited = 0
        report_increment = 5
        while seconds_waited < timeout and self._import_status != "ReadyForImport":
            sleep(report_increment)
            seconds_waited += report_increment
            self._get_import_status()
            logger.debug(
                f"{self.name}: resource import: waited {seconds_waited}sec, "
                f"timeout {timeout}sec, status: {self._import_status}"
            )
        if self._import_status == "ReadyForImport":
            imported = self.api.invoke(
                "Orion.Nodes", "ImportListResourcesResult", self._import_job_id, self.id
            )
            if imported:
                logger.info(
                    f"{self.name}: imported and monitored all SNMP resources (OIDs)"
                )
                self.api.hostname = api_hostname
                # discovery causes new pollers to be added automatically; let's fetch them
                self.pollers.fetch()
                return True
            else:
                self.api.hostname = api_hostname
                raise SWResourceImportError(
                    f"{self.name}: SNMP resource import failed. "
                    "SWIS does not provide any further info."
                )
        else:
            self.api.hostname = api_hostname
            raise SWResourceImportError(
                f"{self.name}: timed out waiting for SNMP resources ({timeout}sec)"
            )

    def remanage(self) -> bool:
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"]:
                self.api.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                logger.info(f"{self.name}: re-managed node")
                self._get_swdata(data="properties", refresh=True)
                return True
            else:
                logger.warning(f"{self.name}: already managed, doing nothing")
                return False
        else:
            logger.warning(f"{self.name}: does not exist, nothing to re-manage")
            return False

    def unmanage(
        self, start: Union[datetime, None] = None, end: Union[datetime, None] = None
    ) -> bool:
        if self.exists():
            now = datetime.utcnow()
            if start is None:
                # accounts for variance in clock synchronization
                start = now - timedelta(minutes=10)
            if end is None:
                end = now + timedelta(days=1)
            self._get_swdata(data="properties")
            if not self._swdata["properties"]["UnManaged"]:
                self.api.invoke(
                    "Orion.Nodes", "Unmanage", f"N:{self.id}", start, end, False
                )
                logger.info(f"{self.name}: unmanaged until {end}")
                self._get_swdata(data="properties", refresh=True)
                return True
            else:
                logger.warning(f"{self.name}: already unmanaged, doing nothing")
                return False
        else:
            logger.warning(f"{self.name}: does not exist, nothing to unmanage")
            return False

    def enforce_icmp_status_polling(self) -> None:
        """ensures that node uses ICMP for up/down status and response time"""
        enable_pollers = [
            "N.Status.ICMP.Native",
            "N.ResponseTime.ICMP.Native",
        ]
        disable_pollers = [
            "N.Status.SNMP.Native",
            "N.ResponseTime.SNMP.Native",
        ]
        logger.info(f"{self}: Enforcing ICMP-based status and response time pollers...")
        for poller_name in enable_pollers:
            poller = self.pollers.get(poller_name)
            if poller:
                if not poller.enabled:
                    poller.enable()
            else:
                self.pollers.add(poller=poller_name, enabled=True)

        for poller_name in disable_pollers:
            poller = self.pollers.get(poller_name)
            if poller:
                if poller.enabled:
                    poller.disable()

    def monitor_resources(
        self,
        pollers: Union[List[str], Literal["all", "none"]] = "all",
        interfaces: Union[
            List[str], Literal["preserve", "up", "all", "none"]
        ] = "preserve",
        volumes: Union[List[str], Literal["preserve", "all", "none"]] = "preserve",
        unmanage_node: bool = True,
        unmanage_node_timeout: int = 60,
        import_timeout: int = 240,
        enforce_icmp_status_polling: bool = True,
        exclude_interfaces: Optional[Union[re.Pattern, List[re.Pattern]]] = None,
    ) -> None:
        """
        Monitors SNMP resources for node.

        Broadly speaking, SNMP resources are those SNMP OIDs that SolarWinds is
        aware of through its installed MIBs.

        SNMP resources belong to three broad and unofficial classes:
        1. System resources, e.g. CPU/RAM, routing tables, and hardware health stats.
        2. System volumes, e.g. any persistent storage device that has a SNMP OID.
        3. Interfaces. These include the usual physical and virtual interfaces you'd
                expect, as well as others you might not, like stack ports, application ports,
                or even more exotic stuff.

        monitor_resources works by invoking the ListResources verbs in SWIS, which imports
        all available resources from all three classes above. These verbs offer no granularity
        whatsoever; they don't even return a list of imported items. There is no way to select
        which resources, volumes, or interfaces you want--you can only import everything,
        then remove any volumes or interfaces you don't want.

        Args:
            pollers: which pollers to enable. May be a list of poller names, or these values:
                all: enable all discovered pollers (default)
                none: disable all discovered pollers
            interfaces: which interfaces to monitor. May be a list of interface names,
                or these values:
                preserve (default): preserves existing interfaces (no net change)
                up: monitor all interfaces that are operationally and administratively up
                all: monitor all interfaces, regardless of their operational or
                    administrative status
                none: exclude all interfaces from monitoring
            volumes: which volumes to monitor. May be a list of volume names, or these
                values:
                preserve (default): preserves existing volumes (no net change)
                all: monitor all available volumes
                none: exclude all volumes from monitoring
            unmanange_node: whether or not to unmanage (unmonitor) the node during
                the resource import process.
            unmanage_node_timeout: maximum time in minutes to unmonitor the node for.
                The node will automatically re-manage itself after this timeout in case
                monitor_resources fails to automatically re-manage the node. In all intended
                cases, the node will be re-managed as soon as resource import has completed.
                This timeout is a failsafe to ensure that a node does not stay unmanaged
                indefinitely if the resource monitoring process fails before re-managing the node.
            import_timeout: maximum time in seconds to wait for SNMP resources to import.
            enforce_icmp_status_polling: SolarWinds recommends using ICMP to monitor status
                (up/down) and response time, which is faster than using SNMP. The ListResources
                verbs, however, automatically enable SNMP-based status and response time pollers.
                To override this and use the recommended ICMP-based status and response time pollers,
                set this to True.
            exclude_interfaces: regex pattern, or list of patterns. If any interface name matches
                any pattern, it will be excluded from monitoring. Does not apply to any interfaces
                provided in interface argument.
        Returns:
            None

        Raises:
            ValueError if node is unmanaged and interfaces == 'up'. When nodes are unmanaged,
                the operational state of all interfaces become unmananged too.
        """
        existing_interface_names = []
        interfaces_to_delete = []
        volumes_to_delete = []

        if interfaces == "up" and unmanage_node:
            raise ValueError("Can't monitor up interfaces when node is unmanaged")

        self._get_swdata(refresh=True)
        already_unmanaged = self.is_unmanaged
        if interfaces == "up" and already_unmanaged:
            raise ValueError("Can't monitor up interfaces when node is unmanaged")

        if unmanage_node:
            if already_unmanaged:
                logger.info(f"{self}: Node is already unmanaged")
            else:
                logger.info(f"{self}: Unmanaging node...")
                self.unmanage(
                    end=(datetime.utcnow() + timedelta(minutes=unmanage_node_timeout))
                )

        if interfaces == "preserve":
            logger.info(f"{self}: Getting existing interfaces to preserve...")
            self.interfaces.get()
            existing_interface_names = [x.name for x in self.interfaces]
            logger.info(
                f"{self} Found {len(existing_interface_names)} existing interfaces"
            )

        if volumes == "preserve":
            logger.info(f"{self}: Getting existing volumes to preserve...")
            existing_volume_names = [x.name for x in self.volumes]
            logger.info(f"{self}: Found {len(existing_volume_names)} existing volumes")

        self.import_snmp_resources(timeout=import_timeout)

        logger.info(f"{self}: Getting imported pollers...")
        self.pollers.fetch()
        logger.info(f"{self}: Found {len(self.pollers)} imported pollers")
        if pollers == "all":
            pass  # all imported pollers are enabled by default
        elif pollers == "none":
            self.pollers.disable_all()
        elif isinstance(pollers, list):
            for poller in self.pollers:
                if poller.name in pollers:
                    if not poller.enabled:
                        poller.enable()
                else:
                    poller.disable()
            for poller_name in pollers:
                poller = self.pollers.get(poller_name)
                if not poller:
                    logger.warning(f"{self}: Poller {poller_name} does not exist")
        else:
            raise ValueError(
                f"{self}: Unexpected value for pollers: {pollers}. "
                'Must be a list of poller names, "all", or "none"'
            )

        logger.info(f"{self}: Getting imported interfaces...")
        self.interfaces.get()
        logger.info(f"{self}: Found {len(self.interfaces)} imported interfaces")
        if interfaces == "preserve":
            interfaces_to_delete = [
                x for x in self.interfaces if x.name not in existing_interface_names
            ]
        elif interfaces == "up":
            interfaces_to_delete = [x for x in self.interfaces if not x.up]
        elif interfaces == "all":
            interfaces_to_delete = []
        elif interfaces == "none":
            interfaces_to_delete = [x for x in self.interfaces]
        elif isinstance(interfaces, List):
            interfaces_to_delete = [
                x for x in self.interfaces if x.name not in interfaces
            ]
        else:
            raise ValueError(
                f"Unexpected value for interfaces: {interfaces}. "
                'Must be a list of interface names, "preserve", "up", "all", or "none"'
            )
        if exclude_interfaces:
            if isinstance(exclude_interfaces, re.Pattern):
                exclude_interfaces = [exclude_interfaces]
            for interface in self.interfaces:
                for pattern in exclude_interfaces:
                    if re.search(pattern, interface.name):
                        logger.debug(
                            f"{self}: excluding interface {interface} because "
                            f'it matches exclusion pattern "{pattern}"'
                        )
                        interfaces_to_delete.append(interface)

        if interfaces_to_delete:
            logger.info(
                f"{self}: Deleting {len(interfaces_to_delete)} extraneous interfaces..."
            )
            self.interfaces.delete(interfaces_to_delete)

        logger.info(f"{self}: Getting imported volumes...")
        self.volumes.fetch()
        if volumes == "preserve":
            volumes_to_delete = [
                x for x in self.volumes if x.name not in existing_volume_names
            ]
        elif volumes == "all":
            volumes_to_delete = []
        elif volumes == "none":
            volumes_to_delete = [x for x in self.volumes]
        elif isinstance(volumes, list):
            volumes_to_delete = [x for x in self.volumes if x.name not in volumes]
        else:
            raise ValueError(
                f"Unexpected value for volumes: {volumes}. "
                'Must be a list of volume names, "preserve", "all", or "none"'
            )
        if volumes_to_delete:
            logger.info(
                f"{self}: Deleting {len(volumes_to_delete)} extraneous volumes..."
            )
            self.volumes.delete(volumes_to_delete)

        if unmanage_node and not already_unmanaged:
            logger.info(f"{self}: re-managing node...")
            self.remanage()

        if enforce_icmp_status_polling:
            self.enforce_icmp_status_polling()

        logger.info(f"{self}: Resource import complete.")

    def save(self) -> bool:
        if self.snmp_version == 3:
            if not self.snmpv3_ro_cred and not self.snmpv3_rw_cred:
                raise SWObjectPropertyError(
                    "must provide either snmpv3_ro_cred or "
                    "snmpv3_rw_cred when snmp_version=3"
                )
        if not self.polling_engine:
            self.polling_engine = OrionEngine(
                api=self.api, id=DEFAULT_POLLING_ENGINE_ID
            )
        self.settings.save()
        return super().save()

    def __repr__(self) -> str:
        return self.name or self.ip_address  # type: ignore

    def __str__(self) -> str:
        return self.name or self.ip_address  # type: ignore


class OrionNodes(object):
    pass
