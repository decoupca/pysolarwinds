from typing import Union

from solarwinds.client import SwisClient
from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.credential import OrionCredential


class OrionNodeSettings(Endpoint):
    endpoint = "Orion.NodeSettings"
    _id_attr = "node_setting_id"
    _swid_key = "NodeSettingID"
    _swquery_attrs = ["node_setting_id"]
    _swargs_attrs = ["node_setting_id"]

    def __init__(
        self,
        swis: SwisClient,
        node_id: int,
        node_setting_id: Union[int, None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ):
        self.swis = swis
        self.node_id = node_id
        self.node_setting_id = node_setting_id
        self.name = name
        self.description = description

        self.snmpv3_ro_creds = None
        self.snmpv3_rw_creds = None

        if node_id is None:
            raise ValueError("must provide `node_id`")
        super().__init__()
