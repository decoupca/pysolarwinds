from pysolarwinds.endpoint import NewEndpoint
from pysolarwinds.swis import SWISClient
from pysolarwinds.endpoints.orion.engines import OrionEngine
from pysolarwinds.endpoints.orion.credential import OrionCredential
from typing import Optional, Union

class OrionNode(NewEndpoint):
    _entity_type = "Orion.Nodes"
    _write_attr_map = {}

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
        # self.polling_engine = polling_engine
        self.snmp_version = snmp_version
        self.snmpv2_ro_community = snmpv2_ro_community
        self.snmpv2_rw_community = snmpv2_rw_community
        self.snmpv3_ro_cred = snmpv3_ro_cred
        self.snmpv3_rw_cred = snmpv3_rw_cred
        self.polling_method = polling_method
