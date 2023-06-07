import datetime
import re
from time import sleep
from typing import Callable, Literal, NewType, Optional, Union

import pysolarwinds.defaults as d
from pysolarwinds.endpoints import Endpoint
from pysolarwinds.endpoints.orion.credentials import Credential, SNMPv2Credential
from pysolarwinds.endpoints.orion.engines import Engine
from pysolarwinds.endpoints.orion.interfaces import InterfaceList
from pysolarwinds.endpoints.orion.pollers import Poller, PollerList
from pysolarwinds.endpoints.orion.volumes import VolumeList
from pysolarwinds.endpoints.orion.worldmap import WorldMapPoint
from pysolarwinds.exceptions import (
    SWAlertSuppressionError,
    SWDiscoveryError,
    SWObjectPropertyError,
    SWResourceImportError,
)
from pysolarwinds.logging import get_logger
from pysolarwinds.maps import NODE_DISCOVERY_STATUS_MAP
from pysolarwinds.models.orion.node_settings import NodeSettings
from pysolarwinds.swis import SWISClient

logger = get_logger(__name__)

DEFAULT_POLLING_ENGINE_ID = 1

Integer = NewType("Integer", int)


class Node(Endpoint):
    endpoint = "Orion.Nodes"
    _type = "node"
    _id_attr = "id"
    _swid_key = "NodeID"
    _swquery_attrs = ["ip_address", "caption"]
    _endpoint_attrs = {
        "polling_engine": Engine,
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
        swis: SWISClient,
        ip_address: Optional[str] = None,
        caption: Optional[str] = None,
        custom_properties: Optional[dict] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        id: Optional[int] = None,
        pollers: Optional[list[str]] = None,
        polling_engine: Union[Engine, int, str, None] = None,
        polling_method: Optional[str] = None,
        snmp_version: Optional[int] = None,
        snmpv2_ro_community: Optional[str] = None,
        snmpv2_rw_community: Optional[str] = None,
        snmpv3_ro_cred: Optional[Credential] = None,
        snmpv3_rw_cred: Optional[Credential] = None,
    ):
        self.swis = swis
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

        self.settings = NodeSettings(node=self)
        self.interfaces = InterfaceList(node=self)

        self._discovery_id = None
        self._discovery_batch_id = None
        self._discovery_status = None
        self._discovery_result = None
        self._discovered_items = None

        self._import_job_id = None
        self._import_status = None
        self._import_response = None

        if self.ip_address is None and self.caption is None:
            raise SWObjectPropertyError("Must provide either ip_address or caption")

        super().__init__()

        self.polling_method = self._get_polling_method()
        self.pollers = PollerList(node=self, enabled_pollers=pollers)
        self.volumes = VolumeList(node=self)

        if self.exists():
            self.settings.fetch()

    @property
    def name(self) -> Optional[str]:
        return self.caption

    @property
    def ints(self) -> InterfaceList:
        return self.interfaces

    @property
    def intf(self) -> InterfaceList:
        return self.interfaces

    @property
    def intfs(self) -> InterfaceList:
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

    def _get_attr_updates(self) -> dict:
        """
        Get attribute updates from swdata
        """
        swdata = self._swdata["properties"]
        return {
            "caption": swdata["Caption"],
            "ip_address": swdata["IPAddress"],
            "snmpv2_ro_community": swdata["Community"],
            "snmpv2_rw_community": swdata["RWCommunity"],
            "polling_engine": Engine(swis=self.swis, id=swdata["EngineID"]),
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
        if not self._discovery_id:
            return None
        query = (
            "SELECT Status FROM Orion.DiscoveryProfiles "
            f"WHERE ProfileID = {self._discovery_id}"
        )
        self._discovery_status = self.swis.query(query)[0]["Status"]

    def _get_import_status(self) -> None:
        if not self._import_job_id:
            return None
        self._import_status = self.swis.invoke(
            "Orion.Nodes",
            "GetScheduledListResourcesStatus",
            self._import_job_id,
            self.id,
        )

    def _get_extra_swargs(self) -> dict:
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
        if self.snmp_version:
            return self.snmp_version
        elif self.snmpv2_ro_community or self.snmpv2_rw_community:
            return 2
        elif self.snmpv3_ro_cred or self.snmpv3_rw_cred:
            return 3
        else:
            return 0

    def create(self) -> bool:
        if not self.ip_address:
            raise SWObjectPropertyError(f"must provide IP address to create node")
        if not self.polling_engine:
            self.polling_engine = Engine(swis=self.swis, id=DEFAULT_POLLING_ENGINE_ID)
        if isinstance(self.polling_engine, int):
            self.polling_engine = Engine(swis=self.swis, id=self.polling_engine)
        if isinstance(self.polling_engine, str):
            self.polling_engine = Engine(swis=self.swis, name=self.polling_engine)
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

    def discover(
        self,
        retries: Integer = 3,
        timeout: Integer = 600,
        protocol: Literal["snmp", "wmi"] = "snmp",
        import_interfaces: Optional[list] = ["up"],
        import_volumes: Optional[bool] = True,
    ) -> bool:
        """
        Runs discovery on node.

        If node does not exist, will discover node with provided IP address and SNMP
        credential(s). Optionally, will also discover pollers, volumes, and interfaces.

        Args:
            retries: Number of SNMP queries to attempt before giving up.
            timeout: Seconds to wait for discovery to complete.
            protocol: Which protocol to use, either snmp or wmi. Only snmp is implemented.
            import_interfaces: NOTE: Currently only works for 'up' or None.
                List of types of interfaces to import. If None is provided,
                no interfaces will be imported. Available options are:
                - up: all up interfaces
                - down: all down interfaces
                - shutdown: all shutdown (administratively disabled) interfaces
                - virtual: all virtual interfaces
                - physical: all physical interfaces
                - trunk: all trunked (802.1q-enabled) interfaces
                - access: all interfaces in standard access mode (not 802.1q-enabled)
                - unknown: all interfaces in unknown status
            import_volumes: Whether or not to keep discovered volumes. By default, the discovery
                verb imports all available volumes, with no known way to tune or filter which
                volumes are imported. This arg provides a convenience to delete all discovered
                volumes after import. TODO: update this arg to allow more options, following the
                example of import_resources()

        Reference: https://github.com/pysolarwinds/OrionSDK/wiki/Discovery
        """
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
            self.polling_engine = Engine(swis=self.swis, id=DEFAULT_POLLING_ENGINE_ID)
        self._resolve_endpoint_attrs()

        credentials = []
        order = 1
        if self.snmp_version == 2:
            if self.snmpv2_rw_community:
                cred = SNMPv2Credential(swis=self.swis, name=self.snmpv2_rw_community)
                if cred.exists():
                    credentials.append({"CredentialID": cred.id, "Order": order})
                    order += 1
            if self.snmpv2_ro_community:
                cred = SNMPv2Credential(swis=self.swis, name=self.snmpv2_ro_community)
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
        core_plugin_config = self.swis.invoke(
            "Orion.Discovery", "CreateCorePluginConfiguration", core_plugin_context
        )
        interface_type_map = {
            "up": "AutoImportStatus",
            "down": "AutoImportStatus",
            "shutdown": "AutoImportStatus",
            "virtual": "AutoImportVirtualTypes",
            "physical": "AutoImportVirtualTypes",
            "trunk": "AutoImportVlanPortTypes",
            "access": "AutoImportVlanPortTypes",
            "unknown": "AutoImportVlanPortTypes",
        }
        interfaces_plugin_context = {
            "AutoImportStatus": [],
            "AutoImportVirtualTypes": [],
            "AutoImportVlanPortTypes": [],
            "UseDefaults": False,
        }
        if import_interfaces is None:
            # No changes to interfaces_plugin_context are needed if not importing
            # any interfaces
            pass
        elif len(import_interfaces) == 1 and "up" in import_interfaces:
            interfaces_plugin_context["UseDefaults"] = True
        else:
            for type in import_interfaces:
                interfaces_plugin_context[interface_type_map[type]].append(
                    type.capitalize()
                )

        interfaces_plugin_config = self.swis.invoke(
            "Orion.NPM.Interfaces",
            "CreateInterfacesPluginConfiguration",
            interfaces_plugin_context,
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
                {"PluginConfigurationItem": interfaces_plugin_config},
            ],
        }
        self._discovery_id = self.swis.invoke(
            "Orion.Discovery", "StartDiscovery", discovery_profile
        )
        logger.info(f"{self}: Discovering node...")
        logger.debug(f"{self.name}: Discovery job ID: {self._discovery_id}")
        self._get_discovery_status()
        seconds_waited = 0
        report_increment = 5
        while seconds_waited < timeout and self._discovery_status == 1:
            sleep(report_increment)
            seconds_waited += report_increment
            self._get_discovery_status()
            logger.debug(
                f"{self}: Discovering... waited {seconds_waited}sec, timeout {timeout}sec, "
                f"status: {NODE_DISCOVERY_STATUS_MAP[self._discovery_status]}"
            )

        if self._discovery_status in (2, 8):
            query = (
                "SELECT Result, ResultDescription, ErrorMessage, BatchID "
                f"FROM Orion.DiscoveryLogs WHERE ProfileID = {self._discovery_id}"
            )
            self._discovery_result = self.swis.query(query)
            result_code = self._discovery_result[0]["Result"]
        else:
            raise SWDiscoveryError(
                f"{self}: Discovery failed. Last reported status: "
                f"{NODE_DISCOVERY_STATUS_MAP[self._discovery_status]}"
            )

        if result_code == 2:
            logger.info(f"{self}: Discovery finished, getting discovered items...")
            self._discovery_batch_id = batch_id = self._discovery_result[0]["BatchID"]
            logger.debug(f"{self}: Discovery batch ID: {batch_id}")
            query = (
                "SELECT EntityType, DisplayName, NetObjectID FROM "
                f"Orion.DiscoveryLogItems WHERE BatchID = '{batch_id}'"
            )
            self._discovered_items = self.swis.query(query) or []
            logger.info(
                f"{self}: Discovered and imported {len(self._discovered_items)} items"
            )
            if not self.exists():
                raise SWDiscoveryError(
                    f"{self}: Discovery completed but node does not exist. "
                    "Check that the provided SNMP credentials are correct, and "
                    "SNMP is reachable from the polling engine "
                    f"({self.polling_engine.ip_address}) to the node "
                    f"({self.ip_address})"
                )
            else:
                # if node didn't exist before discovery, get node uri/id
                self._get_uri()
                self._get_swdata()
                self._get_id()

            if not import_volumes:
                self.volumes.delete_all()

        else:
            error_status = NODE_DISCOVERY_STATUS_MAP[result_code]
            error_message = self._discovery_result[0]["ErrorMessage"]
            result_description = self._discovery_result[0]["ResultDescription"]
            raise SWDiscoveryError(
                f"{self}: Discovery failed. Status: {error_status}, "
                f"error: {error_message or result_description}"
            )

    def import_all_resources(self, timeout=d.IMPORT_RESOURCES_TIMEOUT) -> bool:
        """
        Discovers, imports, and monitors all available SNMP resources.

        In most cases, this will leave the node in an undesirable state (i.e., with
        down interfaces). The more useful method is `import_resources`, which provides a
        means of removing undesired resources after import.

        Args:
            timeout: maximum time in seconds to wait for SNMP resources to import. Generous timeouts
                are recommended in virtually all cases, because allowing pysolarwinds to time out will
                almost certainly leave the node in a state that will generate warnings or alerts due
                to down interfaces or full-capacity storage volumes. In most normal cases, imports
                take about 60-120 seconds. But high latency nodes with many OIDs can take upwards of
                5 minutes, hence the 10 minute (600s) default value.

        Returns:
            True if successful

        Raises:
            SWObjectPropertyError if polling_method is not 'snmp', or if no SNMP
                credentials were provided.
        """
        logger.info(f"{self}: Importing and monitoring all available SNMP resources...")
        if self.polling_method != "snmp":
            raise SWObjectPropertyError(
                f"{self}: Polling_method must be 'snmp' to import resources"
            )
        else:
            if (
                not self.snmpv2_ro_community
                and not self.snmpv2_rw_community
                and not self.snmpv3_ro_cred
                and not self.snmpv3_rw_cred
            ):
                raise SWObjectPropertyError(
                    f"{self}: Must set SNMPv2 community or SNMPv3 credentials"
                )

        # the verbs associated with this method need to be pointed at this
        # node's assigned polling engine. If they are directed at the main SWIS
        # server and the node uses a different polling engine, the process
        # will hang at "unknown" status
        if not isinstance(self.polling_engine, Engine):
            self._resolve_endpoint_attrs()
        swis_hostname = self.swis.hostname
        self.swis.hostname = self.polling_engine.ip_address

        self._import_job_id = self.swis.invoke(
            "Orion.Nodes", "ScheduleListResources", self.id
        )
        logger.debug(f"{self}: Resource import job ID: {self._import_job_id}")
        self._get_import_status()
        seconds_waited = 0
        report_increment = 5
        while seconds_waited < timeout and self._import_status != "ReadyForImport":
            sleep(report_increment)
            seconds_waited += report_increment
            self._get_import_status()
            logger.debug(
                f"{self}: Resource import: waited {seconds_waited}sec, "
                f"timeout {timeout}sec, status: {self._import_status}"
            )
        if self._import_status == "ReadyForImport":
            self._import_response = self.swis.invoke(
                "Orion.Nodes", "ImportListResourcesResult", self._import_job_id, self.id
            )
            if self._import_response:
                logger.info(f"{self}: Imported and monitored all SNMP resources")
                self.swis.hostname = swis_hostname
                # discovery causes new pollers to be added automatically; let's fetch them
                self.pollers.fetch()
                return True
            else:
                self.swis.hostname = swis_hostname
                raise SWResourceImportError(
                    f"{self}: SNMP resource import failed. "
                    "SWIS does not provide any further info, sorry :("
                )
        else:
            self.swis.hostname = swis_hostname
            raise SWResourceImportError(
                f"{self.name}: timed out waiting for SNMP resources ({timeout}sec)"
            )

    def remanage(self) -> bool:
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"]:
                self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
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
                in clock synchronization between the local system and pysolarwinds server. This provides
                greater assurance that a call to `unmanage` will have the expected effect of immediate
                un-management of the node.
            end: optional datetime object, in UTC, at which the node will automatically re-manage
                iteslf. If not provided, defaults to 1 day (86,400 seconds) from start.
            duration: timedelta object representing how long node should remain unmanaged. Defaults
                to 1 day (86,400 seconds).
        """
        if self.exists():
            now = datetime.utcnow()
            if not start:
                start = now - datetime.timedelta(minutes=10)
            if not end:
                end = now + duration
            self._get_swdata(data="properties")
            self.swis.invoke(
                "Orion.Nodes", "Unmanage", f"N:{self.id}", start, end, False
            )
            logger.info(f"{self}: Unmanaged until {end}")
            self._get_swdata(data="properties", refresh=True)
            return True
        else:
            logger.warning(f"{self}: Does not exist; nothing to unmanage")
            return False

    def _get_alert_suppression_state(self) -> dict:
        return self.swis.invoke(
            "Orion.AlertSuppression", "GetAlertSuppressionState", [self.uri]
        )[0]

    @property
    def alerts_are_suppressed(self) -> bool:
        """
        Whether or not alerts are currently suppressed on node.

        """
        return self._get_alert_suppression_state()["SuppressionMode"] == 1

    @property
    def alerts_will_be_suppressed(self) -> bool:
        """
        Whether or not alerts are scheduled to be suppressed at a future
        date/time.

        """
        return self._get_alert_suppression_state()["SuppressionMode"] == 3

    @property
    def alerts_suppressed_from(self) -> Optional[datetime.datetime]:
        """Date/time from when alerts will be suppressed."""
        suppression_state = self._get_alert_suppression_state()
        suppressed_from = suppression_state["SuppressedFrom"]
        if suppressed_from:
            return datetime.strptime(suppressed_from, "%Y-%m-%dT%H:%M:%S")
        else:
            return None

    @property
    def alerts_suppressed_until(self) -> Optional[datetime.datetime]:
        """Date/time from when alerts will be resumed."""
        suppression_state = self._get_alert_suppression_state()
        suppressed_until = suppression_state["SuppressedUntil"]
        if suppressed_until:
            return datetime.strptime(suppressed_until, "%Y-%m-%dT%H:%M:%S")
        else:
            return None

    @property
    def alerts_are_muted(self) -> bool:
        """Convenience alias"""
        return self.alerts_are_suppressed()

    @property
    def alerts_will_be_muted(self) -> bool:
        """Convenience alias"""
        return self.alerts_will_be_suppressed()

    def suppress_alerts(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
    ) -> bool:
        """
        Suppress alerts on node.

        Any alerts that would normally be triggered by any condition(s) on the node
        or its child objects (such as volumes or interfaces), will not be triggered.
        As soon as alerts are resumed, normal alerting behavior resumes.

        Args:
            start: datetime object (in UTC) for when to begin suppressing alerts.
                If omitted, suppression begins immediately.
            end: datetime object (in UTC) for when to resume normal alerting. If
                omitted, alerts will remain suppressed indefinitely.

        Returns: True if successful

        Raises:
            SWAlertSuppressionError if there was an unspecified problem suppressing alerts.
            Under normal conditions, invalid arguments will raise SWISError with details.
        """
        if start is None:
            start = datetime.utcnow() - datetime.timedelta(hours=1)
        # If you provide datetime objects directly to this call, SWIS will
        # erroneously convert it to UTC, so we need to explicitly pass a datetime
        # string in this format: 2023-02-28T16:40:00Z. The trailing "Z" causes
        # SWIS to properly recognize the datetime is in UTC already, and makes
        # no erroneous conversion.
        self.swis.invoke(
            "Orion.AlertSuppression",
            "SuppressAlerts",
            [self.uri],
            datetime.strftime(start, "%Y-%m-%dT%H:%M:%SZ"),
            datetime.strftime(end, "%Y-%m-%dT%H:%M:%SZ") if end else None,
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
        """
        Resume alerts on node immediately. Also cancels planned alert
        suppression, if any.

        Node resumes normal alerting.
        """
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

    @property
    def agent_port(self) -> Optional[int]:
        """Agent port, presumably for SNMP polling."""
        return self._swp.get("AgentPort")

    @property
    def allow_64bit_counters(self) -> bool:
        """Whether or not 64-bit counters are allowed."""
        return self._swp.get("Allow64BitCounters")

    @property
    def avg_response_time(self) -> Optional[int]:
        """Average response time in milliseconds."""
        return self._swp.get("AvgResponseTime")

    @property
    def block_until(self) -> Optional[datetime.datetime]:
        """Unknown meaning."""
        block_until = self._swp.get("BlockUntil")
        if block_until:
            return datetime.strptime(block_until, "%Y-%m-%dT%H:%M:%S")

    @property
    def buffer_big_misses_this_hour(self) -> float:
        """Big buffer misses this hour."""
        return self._swp["BufferBgMissThisHour"]

    @property
    def buffer_big_misses_today(self) -> float:
        """Big buffer misses today."""
        return self._swp["BufferBgMissToday"]

    @property
    def buffer_huge_misses_this_hour(self) -> float:
        """Huge buffer misses this hour."""
        return self._swp["BufferHgMissThisHour"]

    @property
    def buffer_huge_misses_today(self) -> float:
        """Huge buffer misses today."""
        return self._swp["BufferHgMissToday"]

    @property
    def buffer_large_misses_this_hour(self) -> float:
        """Large buffer misses this hour."""
        return self._swp["BufferLgMissThisHour"]

    @property
    def buffer_large_misses_today(self) -> float:
        """Large buffer misses today."""
        return self._swp["BufferLgMissToday"]

    @property
    def buffer_medium_misses_this_hour(self) -> float:
        """Medium buffer misses today."""
        return self._swp["BufferMdMissThisHour"]

    @property
    def buffer_medium_misses_today(self) -> float:
        """Medium buffer misses today."""
        return self._swp["BufferMdMissToday"]

    @property
    def buffer_no_memory_this_hour(self) -> float:
        """Buffer no memory errors this hour."""
        return self._swp["BufferNoMemThisHour"]

    @property
    def buffer_no_memory_today(self) -> float:
        """Buffer no memory errors today."""
        return self._swp["BufferNoMemToday"]

    @property
    def buffer_small_misses_this_hour(self) -> float:
        """Small buffer misses this hour."""
        return self._swp["BufferSmMissThisHour"]

    @property
    def buffer_small_misses_today(self) -> float:
        """Small buffer misses today."""
        return self._swp["BufferSmMissToday"]

    @property
    def cpu_count(self) -> int:
        """Number of CPUs detected on node."""
        return self._swp["CPUCount"]

    @property
    def cpu_load(self) -> int:
        """
        Integer representation of CPU load.

        I would expect this to be a float, but :shrug:
        """
        return self._swp["CPULoad"]

    @property
    def category(self) -> int:
        """Category ID."""
        return self._swp["Category"]

    @property
    def child_status(self) -> int:
        """Child status code."""
        return self._swp["ChildStatus"]

    @property
    def contact(self) -> str:
        """SNMP contact."""
        return self._swp["Contact"]

    @property
    def is_cmts(self) -> bool:
        """Presumably, whether or not node is a cable modem termination system (CMTS)."""
        return self._swp["CMTS"] == "Y"

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

    def import_resources(
        self,
        enable_pollers: Union[None, list[str], Literal["all"]] = "all",
        purge_existing_pollers: bool = False,
        enforce_icmp_status_polling: bool = True,
        monitor_volumes: Union[
            None, list[str], Literal["existing", "all"], Callable
        ] = "existing",
        delete_volumes: Optional[Union[re.Pattern, list[re.Pattern]]] = None,
        monitor_interfaces: Union[
            None, list[str], Literal["existing", "up", "all"], Callable
        ] = "existing",
        delete_interfaces: Optional[Union[re.Pattern, list[re.Pattern]]] = None,
        unmanage_node: bool = True,
        unmanage_node_timeout: Union[datetime.timedelta, int] = datetime.timedelta(
            days=d.IMPORT_RESOURCES_UNMANAGE_NODE_DAYS
        ),
        remanage_delay: Optional[Union[datetime.timedelta, int]] = None,
        import_timeout: int = d.IMPORT_RESOURCES_TIMEOUT,
    ) -> None:
        """
        Imports and monitors SNMP resources.

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
            enable_pollers: which pollers to enable. May be a list of poller names, or these values:
                all: enable all discovered pollers (default)
                None: disable all discovered pollers (i.e., delete all discovered pollers)
            purge_existing_pollers: whether or not to delete all existing pollers before discovering/
                enabling all available pollers. Useful if existing pollers might be incorrect. Use
                caution when enabling this in a concurrent/threaded scenario; see warning above.
            monitor_interfaces: which interfaces to monitor. May be a list of interface names,
                None, a callable object, or one of: 'existing', 'up', 'all'.
                existing (default): preserves existing interfaces (no net change to interfaces)
                up: Monitor all interfaces that SolarWinds reports as operationally and
                    administratively up
                all: Monitor all interfaces, regardless of their operational or
                    administrative status
                None: Do not monitor any interfaces (i.e., delete all imported interfaces)
                If a callable is provided, the interface will be provided as the only argument and
                the interface will be monitored if it returns a truthy response.
            monitor_volumes: which volumes to monitor. May be a list of volume names, a callable
                object, or one of: 'existing', 'all':
                existing (default): preserves existing volumes (no net change)
                all: Monitor all available volumes
                None: Do not monitor any volumes (i.e., delete all imported volumes)
                If a callable is provided, the volume will be provided as the only argument and
                the volume will be monitored if it returns a truthy response.
            unmanange_node: whether or not to unmanage (unmonitor) the node during
                the resource import process. The ListResources verbs import all available OIDs
                and interfaces, including any in a down or error state. Unmanaging the node before
                import may mitigate this. Be aware: for this to help, your alert definitions must
                account for node status. In other words, if your alert definition for interface
                down only considers the interface status, then unmanaging the node will have no
                protective effect on preventing false positive interface down alerts.
            unmanage_node_timeout: maximum time to unmonitor the node for. May be a
                datetime.timedelta object, or an integer for seconds.
                The node will automatically re-manage itself after this timeout in case
                monitor_resources fails to automatically re-manage the node. In all intended
                cases, the node will be re-managed as soon as resource import has completed.
                This timeout is a failsafe to ensure that a node does not stay unmanaged
                indefinitely if the resource monitoring process fails before re-managing the node.
            remanage_delay: after successful resource import, delay re-managing node for this
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
            import_timeout: maximum time in seconds to wait for SNMP resources to import. Generous timeouts
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
            delete_interfaces: regex pattern, or list of patterns. If any interface name matches
                any pattern, it will be excluded from monitoring.
            delete_volumes: regex pattern, or list of patterns. If any volume name matches
                any pattern, it will be excluded from monitoring.

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
            raise ValueError("Can't monitor up interfaces when node is unmanaged")

        self._get_swdata(refresh=True)
        already_unmanaged = self.is_unmanaged
        if monitor_interfaces == "up" and already_unmanaged:
            raise ValueError("Can't monitor up interfaces when node is unmanaged")

        if unmanage_node:
            if already_unmanaged:
                logger.info(f"{self}: Node is already unmanaged")
            else:
                logger.info(f"{self}: Unmanaging node...")
                if isinstance(unmanage_node_timeout, datetime.timedelta):
                    delta = unmanage_node_timeout
                elif isinstance(unmanage_node_timeout, int):
                    delta = datetime.timedelta(seconds=unmanage_node_timeout)
                else:
                    raise ValueError(
                        "Unexpected value for unmanage_node_timeout: "
                        f"{unmanage_node_timeout}. Must be either a positive integer (seconds) "
                        "datetime.timedelta object"
                    )
                self.unmanage(end=(datetime.utcnow() + delta))

        if monitor_interfaces == "existing":
            logger.info(f"{self}: Getting existing interfaces to preserve...")
            self.interfaces.fetch()
            existing_interface_names = [x.name for x in self.interfaces]
            logger.info(
                f"{self} Found {len(existing_interface_names)} existing interfaces"
            )

        if monitor_volumes == "existing":
            logger.info(f"{self}: Getting existing volumes to preserve...")
            existing_volume_names = [x.name for x in self.volumes]
            logger.info(f"{self}: Found {len(existing_volume_names)} existing volumes")

        if purge_existing_pollers:
            logger.info(f"{self}: Purging existing pollers...")
            self.pollers.fetch()
            self.pollers.delete_all()

        self.import_all_resources(timeout=import_timeout)

        logger.info(f"{self}: Getting imported pollers...")
        self.pollers.fetch()
        logger.info(f"{self}: Found {len(self.pollers)} imported pollers")
        if enable_pollers == "all":
            pass  # all imported pollers are enabled by default
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
                    logger.warning(f"{self}: Poller {poller_name} does not exist")
        else:
            raise ValueError(
                f"{self}: Unexpected value for pollers: {enable_pollers}. "
                'Must be a list of poller names, "all", or None'
            )

        logger.info(f"{self}: Getting imported interfaces...")
        self.interfaces.fetch()
        logger.info(f"{self}: Found {len(self.interfaces)} imported interfaces")
        if monitor_interfaces == "existing":
            interfaces_to_delete = [
                x for x in self.interfaces if x.name not in existing_interface_names
            ]
        elif monitor_interfaces == "up":
            interfaces_to_delete = [x for x in self.interfaces if not x.up]
        elif monitor_interfaces == "all":
            interfaces_to_delete = []
        elif monitor_interfaces is None:
            interfaces_to_delete = [x for x in self.interfaces]
        elif isinstance(monitor_interfaces, list):
            interfaces_to_delete = [
                x for x in self.interfaces if x.name not in monitor_interfaces
            ]
        elif callable(monitor_interfaces):
            interfaces_to_delete = [
                x for x in self.interfaces if not monitor_interfaces(x)
            ]
        else:
            raise ValueError(
                f"Unexpected value for monitor_interfaces: {monitor_interfaces}. "
                "Must be a list of interface names, a callable, or one of these values: "
                '"existing", "up", "all", or None'
            )
        if delete_interfaces:
            if isinstance(delete_interfaces, re.Pattern):
                delete_interfaces = [delete_interfaces]
            for interface in self.interfaces:
                for pattern in delete_interfaces:
                    if re.search(pattern, interface.name):
                        logger.debug(
                            f"{self}: excluding interface {interface} because "
                            f'it matches exclusion pattern "{pattern}"'
                        )
                        interfaces_to_delete.append(interface)

        if interfaces_to_delete:
            interfaces_to_delete = list(set(interfaces_to_delete))
            logger.info(
                f"{self}: Deleting {len(interfaces_to_delete)} unwanted interfaces..."
            )
            self.interfaces.delete(interfaces_to_delete)

        logger.info(f"{self}: Getting imported volumes...")
        self.volumes.fetch()
        if monitor_volumes == "existing":
            volumes_to_delete = [
                x for x in self.volumes if x.name not in existing_volume_names
            ]
        elif monitor_volumes == "all":
            volumes_to_delete = []
        elif monitor_volumes is None:
            volumes_to_delete = [x for x in self.volumes]
        elif isinstance(monitor_volumes, list):
            volumes_to_delete = [
                x for x in self.volumes if x.name not in monitor_volumes
            ]
        elif callable(monitor_volumes):
            volumes_to_delete = [x for x in self.volumes if not monitor_volumes(x)]
        else:
            raise ValueError(
                f"Unexpected value for monitor_volumes: {monitor_volumes}. "
                "Must be a list of volume names, a callable, or one of these values: "
                '"existing", "all", None'
            )
        if delete_volumes:
            if isinstance(delete_volumes, re.Pattern):
                delete_volumes = [delete_volumes]
            for volume in self.volumes:
                for pattern in delete_volumes:
                    if re.search(pattern, volume.name):
                        logger.debug(
                            f"{self}: excluding volume {volume} because "
                            f'it matches exclusion pattern "{pattern}"'
                        )
                        volumes_to_delete.append(volume)
        if volumes_to_delete:
            logger.info(
                f"{self}: Deleting {len(volumes_to_delete)} unwanted volumes..."
            )
            self.volumes.delete(volumes_to_delete)

        if unmanage_node and not already_unmanaged:
            if remanage_delay:
                if isinstance(remanage_delay, int):
                    delta = datetime.timedelta(seconds=remanage_delay)
                    msg = f"setting node to re-manage in {remanage_delay}sec..."
                else:
                    delta = remanage_delay
                    msg = f"delaying re-manage by {remanage_delay}..."
                logger.info(f"{self}: {msg}")
                self.unmanage(end=(datetime.utcnow() + delta))
            else:
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
            self.polling_engine = Engine(swis=self.swis, id=DEFAULT_POLLING_ENGINE_ID)
        self.settings.save()
        return super().save()

    def __repr__(self) -> str:
        return self.name or self.ip_address  # type: ignore

    def __str__(self) -> str:
        return self.name or self.ip_address  # type: ignore


class Nodes(object):
    pass
