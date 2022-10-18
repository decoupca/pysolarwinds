from datetime import datetime, timedelta
from logging import NullHandler, getLogger
from time import sleep
from typing import Dict, List, Union

import solarwinds.defaults as d
from solarwinds.client import SwisClient
from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.endpoints.orion.interface import OrionInterfaces
from solarwinds.endpoints.orion.worldmap import WorldMapPoint
from solarwinds.exceptions import SWNodeDiscoveryError, SWObjectPropertyError

log = getLogger(__name__)
log.addHandler(NullHandler())

NODE_DISCOVERY_STATUS_MAP = {
    0: "unknown",
    1: "in_progress",
    2: "finished",
    3: "error",
    4: "not_scheduled",
    5: "scheduled",
    6: "not_completed",
    7: "canceling",
    8: "ready_for_import",
}


class OrionNode(Endpoint):
    endpoint = "Orion.Nodes"
    _id_attr = "node_id"
    _swid_key = "NodeID"
    _swquery_attrs = ["ip_address", "caption"]
    _swargs_attrs = [
        "caption",
        "engine_id",
        "ip_address",
        "snmp_version",
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
        "snmpv3_ro_creds": {
            "class": OrionCredential,
            "init_args": {
                "snmpv3_ro_cred_name": "name",
            },
            "attr_map": {
                "snmpv3_ro_cred_id": "id",
            },
        },
        "snmpv3_rw_creds": {
            "class": OrionCredential,
            "init_args": {
                "snmpv3_rw_cred_name": "name",
            },
            "attr_map": {
                "snmpv3_rw_cred_id": "id",
            },
        },
    }

    def __init__(
        self,
        swis: SwisClient,
        ip_address: Union[str, None] = None,
        caption: Union[str, None] = None,
        custom_properties: Union[Dict, None] = None,
        engine_id: Union[int, None] = None,
        latitude: Union[float, None] = None,
        longitude: Union[float, None] = None,
        node_id: Union[int, None] = None,
        pollers: Union[List, None] = None,
        polling_method: Union[str, None] = None,
        snmp_version: Union[int, None] = None,
        snmpv2c_ro_community: Union[str, None] = None,
        snmpv2c_rw_community: Union[str, None] = None,
        snmpv3_ro_cred_name: Union[str, None] = None,
        snmpv3_rw_cred_name: Union[str, None] = None,
    ):
        self.swis = swis
        self.caption = caption
        self.engine_id = engine_id or 1
        self.custom_properties = custom_properties
        self.ip_address = ip_address
        self.latitude = latitude
        self.longitude = longitude
        self.node_id = node_id
        self.polling_method = polling_method
        self.pollers = pollers
        self.snmp_version = snmp_version
        self.snmpv2c_ro_community = snmpv2c_ro_community
        self.snmpv2c_rw_community = snmpv2c_rw_community
        self.snmpv3_ro_cred_name = snmpv3_ro_cred_name
        self.snmpv3_rw_cred_name = snmpv3_rw_cred_name

        self.map_point = None
        self.snmpv3_ro_creds = None
        self.snmpv3_rw_creds = None
        self.snmpv3_ro_cred_id = None
        self.snmpv3_rw_cred_id = None

        self.interfaces = OrionInterfaces(self)

        self._discovery_profile_id = None
        self._discovery_profile_status = 0
        self._discovered_entities = None

        self._swdata = {}

        if self.ip_address is None and self.caption is None:
            raise SWObjectPropertyError("Must provide either ip_address or caption")

        if (
            snmp_version == 3
            and snmpv3_ro_cred_name is None
            and snmpv3_rw_cred_name is None
        ):
            raise ValueError(
                "must provide either `snmpv3_ro_cred_name` or "
                "`snmpv3_rw_cred_name` when `snmp_version` = 3"
            )
        super().__init__()

    @property
    def name(self) -> Union[str, None]:
        return self.caption

    @property
    def int(self):
        return self.interfaces

    @property
    def ints(self):
        return self.interfaces

    @property
    def intf(self):
        return self.interfaces

    @property
    def intfs(self):
        return self.interfaces

    @property
    def ip(self) -> Union[str, None]:
        return self.ip_address

    @ip.setter
    def ip(self, ip_address: str) -> None:
        self.ip_address = ip_address

    @property
    def hostname(self) -> Union[str, None]:
        return self.caption

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.caption = hostname

    @property
    def status(self):
        return self._get_swdata_value("Status")

    def _associate_credential_set(self, cred_type: str, cred_id: int) -> bool:  # type: ignore
        """
        Create association between node and SNMPv3 credential set
        NOTE: this approach was advised by a Solarwinds senior engineer and uses
        a workaround which uses TSQL syntax, **NOT** the usual SWQL syntax
        (notice the table refrence is "NodeSettings", not "Orion.NodeSettings")
        """
        statement = (
            "INSERT INTO NodeSettings (NodeID, SettingName, SettingValue) VALUES "
            f"('{self.node_id}', '{cred_type}', '{cred_id}')"
        )
        self.swis.sql(statement)
        log.debug(f"SNMPv3: assigned credential type {cred_type} with ID {cred_id}")
        return True

    def _set_defaults(self) -> None:
        if self.polling_method is None:
            if (
                self.snmpv2c_ro_community is not None
                or self.snmpv2c_rw_community is not None
            ):
                self.polling_method = "snmp"
                self.snmp_version = 2
            elif (
                self.snmpv3_ro_cred_name is not None
                or self.snmpv3_rw_cred_name is not None
            ):
                self.polling_method = "snmp"
                self.snmp_version = 3
            else:
                self.polling_method = "icmp"
                self.snmp_version = 0
        if self.pollers is None:
            self.pollers = d.NODE_DEFAULT_POLLERS[self.polling_method]

    def _get_attr_updates(self) -> Dict:
        """
        Get attribute updates from swdata
        """
        swdata = self._swdata["properties"]
        return {
            "caption": swdata["Caption"],
            "ip_address": swdata["IPAddress"],
            "engine_id": swdata["EngineID"],
            "snmpv2c_ro_community": swdata["Community"],
            "snmpv2c_rw_community": swdata["RWCommunity"],
            "polling_method": self._get_polling_method(),
            "pollers": self.pollers
            or d.NODE_DEFAULT_POLLERS[swdata["ObjectSubType"].lower()],
            "snmp_version": swdata["SNMPVersion"],
        }

    def _get_discovery_status(self) -> None:
        if self._discovery_profile_id is None:
            return None
        status_query = f"SELECT Status FROM Orion.DiscoveryProfiles WHERE ProfileID = {self._discovery_profile_id}"
        self._discovery_profile_status = self.swis.query(status_query)["Status"]

    def _get_extra_swargs(self) -> Dict:
        return {
            "status": self._get_swdata_value("Status") or 1,
            "objectsubtype": self._get_polling_method().upper(),
        }

    def _get_polling_method(self) -> str:
        ro_community = self._get_swdata_value("Community") or self.snmpv2c_ro_community
        rw_community = (
            self._get_swdata_value("RWCommunity") or self.snmpv2c_rw_community
        )
        if ro_community is not None or rw_community is not None or self.snmp_version:
            return "snmp"
        else:
            return "icmp"

    def _get_pollers(self) -> Union[List, None]:
        if self.polling_method is not None:
            return d.NODE_DEFAULT_POLLERS[self.polling_method]
        else:
            return None

    def _get_snmp_version(self):
        if (
            self.snmpv2c_ro_community is not None
            or self.snmpv2c_rw_community is not None
        ):
            return 2
        elif (
            self.snmpv3_ro_cred_name is not None or self.snmpv3_rw_cred_name is not None
        ):
            return 3
        else:
            return 0

    def enable_pollers(self) -> bool:
        node_id = self.node_id or self._get_id()
        if self.pollers is None:
            log.warning(f"no pollers to enable, doing nothing")
            return False
        else:
            for poller_type in self.pollers:
                poller = {
                    "PollerType": poller_type,
                    "NetObject": f"N:{node_id}",
                    "NetObjectType": "N",
                    "NetObjectID": node_id,
                    "Enabled": True,
                }
                self.swis.create("Orion.Pollers", **poller)
                log.info(f"enabled poller {poller_type}")
            return True

    def create(self) -> bool:
        if self.snmp_version == 3:
            if self.snmpv3_ro_cred_name is None and self.snmpv3_rw_cred_name is None:
                raise ValueError(
                    "must provide `snmpv3_ro_cred_name` or `snmpv3_rw_cred_name` when `snmp_version` = 3"
                )
            # creating nodes with a saved credential set requires discovery
            # https://thwack.solarwinds.com/product-forums/the-orion-platform/f/orion-sdk/25327/using-orion-credential-set-for-snmpv3-when-adding-node-through-sdk/25220#25220
            # TODO: it is possible to directly create an snmpv3 node using ad-hoc credentials
            #       (i.e, not referencing a saved credential set), but this is not yet implemented.
            created = self.discover()
            if created is True:
                # discovery will not apply any extra params passed to node object,
                # such as custom properties
                self.update()
        else:
            created = super().create()
        if created is True:
            self.enable_pollers()
        return created

    def discover(self, retries=None, timeout=None) -> bool:
        if retries is None:
            retries = d.NODE_DISCOVERY_SNMP_RETRIES
        if timeout is None:
            timeout = d.NODE_DISCOVERY_JOB_TIMEOUT_SECONDS

        credentials = []
        order = 1
        if self.snmpv3_ro_cred_id is not None:
            credentials.append(
                {
                    "CredentialID": self.snmpv3_ro_cred_id,
                    "Order": order,
                }
            )
            order += 1
        if self.snmpv3_rw_cred_id is not None:
            credentials.append(
                {
                    "CredentialID": self.snmpv3_rw_cred_id,
                    "Order": order,
                }
            )

        core_plugin_context = {
            "BulkList": [{"Address": self.ip_address}],
            "Credentials": credentials,
            "WmiRetriesCount": 0,
            "WmiRetryIntervalMiliseconds": 1000,
        }
        core_plugin_config = self.swis.invoke(
            "Orion.Discovery", "CreateCorePluginConfiguration", core_plugin_context
        )
        discovery_profile = {
            "Name": f"Discover {self.name}",
            "EngineId": self.engine_id,
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
        self._discovery_profile_id = self.swis.invoke(
            "Orion.Discovery", "StartDiscovery", discovery_profile
        )
        log.debug(f"node discovery: job id: {self._discovery_profile_id}")
        self._get_discovery_status()
        seconds_waited = 0
        while seconds_waited < timeout and self._discovery_profile_status == 1:
            sleep(1)
            seconds_waited += 1
            self._get_discovery_status()
            log.debug(
                f"discovering node: waited {seconds_waited}sec, timeout {timeout}sec, "
                f"status: {NODE_DISCOVERY_STATUS_MAP[self._discovery_profile_status]}"
            )

        if self._discovery_profile_status == 2:
            result_query = f"SELECT Result, ResultDescription, ErrorMessage, BatchID FROM Orion.DiscoveryLogs WHERE ProfileID = {self._discovery_profile_id}"
            result = self.swis.query(result_query)
            result_code = result["Result"]
        else:
            raise SWNodeDiscoveryError(
                f"node discovery failed. last status: {NODE_DISCOVERY_STATUS_MAP[self._discovery_profile_status]}"
            )

        if result_code == 2:
            log.debug(f"node discovery job finished, getting discovered items...")
            batch_id = result["BatchID"]
            discovered_query = f"SELECT EntityType, DisplayName, NetObjectID FROM Orion.DiscoveryLogItems WHERE BatchID = '{batch_id}'"
            self._discovered_entities = self.swis.query(discovered_query)
            if self._discovered_entities is not None:
                return True
            else:
                return False
        else:
            error_status = NODE_DISCOVERY_STATUS_MAP[result_code]
            error_message = result["ErrorMessage"]
            raise SWNodeDiscoveryError(
                f"node discovery failed. status: {error_status}, error: {error_message}"
            )

    def remanage(self) -> bool:
        if self.exists():
            self._get_swdata(data="properties")
            if self._swdata["properties"]["UnManaged"] is True:
                self.swis.invoke("Orion.Nodes", "Remanage", f"N:{self.id}")
                log.info(f"re-managed node successfully")
                return True
            else:
                log.warning(f"node is already managed, doing nothing")
                return False
        else:
            log.warning(f"node does not exist, can't remanage")
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
            if self._swdata["properties"]["UnManaged"] is False:
                self.swis.invoke(
                    "Orion.Nodes", "Unmanage", f"N:{self.node_id}", start, end, False
                )
                log.info(f"unmanaged node until {end}")
                return True
            else:
                log.warning(f"node is already unmanaged, doing nothing")
                return False
        else:
            log.warning(f"node does not exist, can't unmanage")
            return False

    def update(self):
        # changing a node from snmpv2c to snmpv3 takes some special handholding
        if (
            self.snmp_version == 3
            and self._swdata["properties"].get("SNMPVersion") == 2
        ):
            if self.snmpv3_ro_cred_name is None and self.snmpv3_rw_cred_name is None:
                raise ValueError(
                    "must provide either `snmpv3_ro_cred_name` or "
                    "`snmpv3_rw_cred_name` when `snmp_version` = 3"
                )

            if self.snmpv3_ro_cred_name is not None:
                if self.snmpv3_ro_cred_id is None:
                    self._init_child_objects()
                    self._update_attrs_from_children()
                self._associate_credential_set(
                    "ROSNMPCredentialID", self.snmpv3_ro_cred_id
                )

            if self.snmpv3_rw_cred_name is not None:
                if self.snmpv3_rw_cred_id is None:
                    self._init_child_objects()
                    self._update_attrs_from_children()
                self._associate_credential_set(
                    "RWSNMPCredentialID", self.snmpv3_rw_cred_id
                )

        # clear stale credential association(s) if switching from v3 to v2
        if (
            self.snmp_version == 2
            and self._swdata["properties"].get("SNMPVersion") == 3
        ):
            statement = f"DELETE FROM NodeSettings WHERE NodeID = '{self.node_id}' AND (SettingName = 'ROSNMPCredentialID' OR SettingName = 'RWSNMPCredentialID')"
            self.swis.sql(statement)
            log.debug(f"SNMPv3: deleted all associated SNMPv3 credential sets")

        super().update()

    def __repr__(self) -> str:
        return self.name or self.ip_address  # type: ignore

    def __str__(self) -> str:
        return self.name or self.ip_address  # type: ignore


class OrionNodes(object):
    pass
