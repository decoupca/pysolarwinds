from datetime import datetime, timedelta
from time import sleep
from typing import Dict, List, Optional, Union

import solarwinds.defaults as d
from solarwinds.api import API
from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.endpoints.orion.engines import OrionEngine
from solarwinds.endpoints.orion.interface import OrionInterfaces
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
        "snmpv2c_ro_community": "Community",
        "snmpv2c_rw_community": "RWCommunity",
    }
    _swargs_attrs = [
        "caption",
        "ip_address",
        "snmp_version",
        "snmpv2c_ro_community",
        "snmpv2c_rw_community",
    ]
    _required_swargs_attrs = ["ip_address", "engine_id"]
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
        pollers: Optional[List] = None,
        polling_engine: Union[OrionEngine, int, str, None] = None,
        polling_method: Optional[str] = None,
        snmp_version: Optional[int] = None,
        snmpv2c_ro_community: Optional[str] = None,
        snmpv2c_rw_community: Optional[str] = None,
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
        self.polling_method = polling_method
        self.pollers = pollers
        self.snmp_version = snmp_version
        self.snmpv2c_ro_community = snmpv2c_ro_community
        self.snmpv2c_rw_community = snmpv2c_rw_community
        self.snmpv3_ro_cred = snmpv3_ro_cred
        self.snmpv3_rw_cred = snmpv3_rw_cred

        self.map_point = None

        self.settings = OrionNodeSettings(self)
        self.interfaces = OrionInterfaces(self)

        self._discovery_profile_id = None
        self._discovery_profile_status = 0
        self._discovered_entities = None

        self._import_job_id = None
        self._import_status = None

        if self.ip_address is None and self.caption is None:
            raise SWObjectPropertyError("Must provide either ip_address or caption")

        super().__init__()

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
    def status(self) -> Optional[str]:
        return self._swp.get("Status")

    def _set_defaults(self) -> None:
        if not self.polling_method:
            if self.snmpv2c_ro_community or self.snmpv2c_rw_community:
                self.polling_method = "snmp"
                self.snmp_version = 2
            elif self.snmpv3_ro_cred or self.snmpv3_rw_cred:
                self.polling_method = "snmp"
                self.snmp_version = 3
            else:
                self.polling_method = "icmp"
                self.snmp_version = 0
        if not self.pollers:
            self.pollers = d.NODE_DEFAULT_POLLERS[self.polling_method.lower()]

    def _get_attr_updates(self) -> Dict:
        """
        Get attribute updates from swdata
        """
        swdata = self._swdata["properties"]
        return {
            "caption": swdata["Caption"],
            "ip_address": swdata["IPAddress"],
            "snmpv2c_ro_community": swdata["Community"],
            "snmpv2c_rw_community": swdata["RWCommunity"],
            "polling_engine": OrionEngine(api=self.api, id=swdata["EngineID"]),
            "polling_method": self._get_polling_method(),
            "pollers": self._get_pollers()
            or d.NODE_DEFAULT_POLLERS[swdata["ObjectSubType"].lower()],
            "snmp_version": swdata["SNMPVersion"],
        }

    def _build_swargs(self) -> None:
        swargs = {"properties": None, "custom_properties": None}
        properties = {
            "Caption": self.caption,
            "IPAddress": self.ip_address,
            "Community": self.snmpv2c_ro_community,
            "RWCommunity": self.snmpv2c_rw_community,
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
                self._swdata["properties"].get("Community") or self.snmpv2c_ro_community
            )
            rw_community = (
                self._swdata["properties"].get("RWCommunity")
                or self.snmpv2c_rw_community
            )
            if ro_community or rw_community or self.snmp_version != 0:
                return "snmp"
            else:
                return "icmp"
        else:
            return self.polling_method

    def _get_pollers(self) -> List:
        """get a list of solarwinds pollers to enable"""
        return d.NODE_DEFAULT_POLLERS.get(self.polling_method) or []

    def _get_snmp_version(self) -> int:
        if self.snmpv2c_ro_community or self.snmpv2c_rw_community:
            return 2
        elif self.snmpv3_ro_cred or self.snmpv3_rw_cred:
            return 3
        else:
            return 0

    def enable_pollers(self) -> bool:
        id = self.id or self._get_id()
        if not self.pollers:
            logger.warning(f"no pollers to enable, doing nothing")
            return False
        else:
            for poller_type in self.pollers:
                poller = {
                    "PollerType": poller_type,
                    "NetObject": f"N:{id}",
                    "NetObjectType": "N",
                    "NetObjectID": id,
                    "Enabled": True,
                }
                self.api.create("Orion.Pollers", **poller)
                logger.info(f"enabled poller {poller_type}")
            return True

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
            self.enable_pollers()
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
            not self.snmpv2c_ro_community
            and not self.snmpv2c_rw_community
            and not self.snmpv3_ro_cred
            and not self.snmpv3_rw_cred
        ):
            raise SWObjectPropertyError(
                "Discovery requires at least one SNMP credential property set: "
                "snmpv2c_ro_community, snmpv2c_rw_community, snmpv3_ro_cred, or snmpv3_rw_cred"
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
        if self.snmpv3_ro_cred:
            credentials.append(
                {
                    "CredentialID": self.snmpv3_ro_cred.id,
                    "Order": order,
                }
            )
            order += 1
        if self.snmpv3_rw_cred:
            credentials.append(
                {
                    "CredentialID": self.snmpv3_rw_cred.id,
                    "Order": order,
                }
            )

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
                raise SWDiscoveryError(
                    f"{self.name}: discovery found nothing at IP: {self.ip_address}"
                )
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
        logger.info(f"{self.name}: importing all SNMP resources...")
        if self.polling_method != "snmp":
            raise SWObjectPropertyError(
                f"{self.name}: polling_method must be 'snmp' to import resources"
            )
        else:
            if (
                not self.snmpv2c_ro_community
                and not self.snmpv2c_rw_community
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
                logger.info(f"{self.name}: imported all SNMP resources")
                self.api.hostname = api_hostname
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
                f"{self.name}: timed out waiting for SNMP resources"
            )

    def remanage(self) -> bool:
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"]:
                self.api.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                logger.info(f"{self.name}: re-managed node")
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
                return True
            else:
                logger.warning(f"{self.name}: already unmanaged, doing nothing")
                return False
        else:
            logger.warning(f"{self.name}: does not exist, nothing to unmanage")
            return False

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
