from typing import Dict, List, Optional, Union

from pysolarwinds.endpoints.orion.credential import OrionCredential
from pysolarwinds.endpoints.orion.engines import OrionEngine
from pysolarwinds.endpoints.orion.node import OrionNode
from pysolarwinds.models.orion.credential import Credential
from pysolarwinds.models.orion.worldmap import WorldMap


class Orion:
    def __init__(self, swis):
        self.swis = swis
        self.worldmap = WorldMap(swis=swis)
        self.credential = Credential(swis=swis)

    def engine(
        self,
        id: Optional[int] = None,
        ip_address: Optional[str] = None,
        name: Optional[str] = None,
    ) -> OrionEngine:
        return OrionEngine(swis=self.swis, id=id, ip_address=ip_address, name=name)

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
            swis=self.swis,
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
