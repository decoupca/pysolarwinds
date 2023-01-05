from typing import Dict, List, Optional, Union

from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.endpoints.orion.engines import OrionEngine
from solarwinds.endpoints.orion.node import OrionNode
from solarwinds.models.orion.credential import Credential
from solarwinds.models.orion.worldmap import WorldMap


class Orion:
    def __init__(self, api):
        self.api = api
        self.worldmap = WorldMap(api=api)
        self.credential = Credential(api=api)

    def engine(
        self,
        id: Optional[int] = None,
        ip_address: Optional[str] = None,
        name: Optional[str] = None,
    ) -> OrionEngine:
        return OrionEngine(api=self.api, id=id, ip_address=ip_address, name=name)

    def node(
        self,
        ip_address: Optional[str] = None,
        caption: Optional[str] = None,
        custom_properties: Optional[Dict] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        id: Optional[int] = None,
        pollers: Optional[List] = None,
        polling_engine: Union[OrionEngine, str, int, None] = None,
        polling_method: Optional[str] = None,
        snmp_version: Optional[int] = None,
        snmpv2_ro_community: Optional[str] = None,
        snmpv2_rw_community: Optional[str] = None,
        snmpv3_ro_cred: Optional[OrionCredential] = None,
        snmpv3_rw_cred: Optional[OrionCredential] = None,
    ) -> OrionNode:
        return OrionNode(
            api=self.api,
            ip_address=ip_address,
            caption=caption,
            custom_properties=custom_properties,
            latitude=latitude,
            longitude=longitude,
            id=id,
            pollers=pollers,
            polling_engine=polling_engine,
            polling_method=polling_method,
            snmp_version=snmp_version,
            snmpv2_ro_community=snmpv2_ro_community,
            snmpv2_rw_community=snmpv2_rw_community,
            snmpv3_ro_cred=snmpv3_ro_cred,
            snmpv3_rw_cred=snmpv3_rw_cred,
        )
