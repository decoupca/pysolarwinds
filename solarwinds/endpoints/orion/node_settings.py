from typing import Dict

from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.credential import OrionCredential


class OrionNodeSetting(Endpoint):
    endpoint = "Orion.NodeSettings"

    def __init__(self, node, setting: Dict):
        self.node = node
        self.swis = node.swis
        self._dict = setting
        self.id = setting.get("NodeSettingID")
        self.name = setting["SettingName"]
        self.value = setting["SettingValue"]

        if self.name in ["ROSNMPCredentialID", "RWSNMPCredentialID"]:
            self.setting = OrionCredential(
                swis=self.swis, node_id=self.node.id, id=self.value
            )

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class OrionNodeSettings(object):
    def __init__(self, node):
        self.node = node
        self.swis = node.swis
        self._settings = []

        query = f"SELECT SettingName, SettingValue, NodeSettingID FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}'"
        settings = self.swis.query(query)
        if settings is not None:
            for setting in settings:
                name = setting["SettingName"]
                value = setting["SettingValue"]

                if name in ["ROSNMPCredentialID", "RWSNMPCredentialID"]:
                    cred = OrionCredential(
                        swis=self.swis, node_id=self.node.id, id=value
                    )
                    self._settings.append(cred)
                    if name == "ROSNMPCredentialID" and cred.credential_type.endswith(
                        "SnmpCredentialsV3"
                    ):
                        self.node.snmpv3_ro_cred_name = cred.name
                        self.node.snmpv3_ro_cred_id = cred.id
                    if name == "RWSNMPCredentialID" and cred.credential_type.endswith(
                        "SnmpCredentialsV3"
                    ):
                        self.node.snmpv3_rw_cred_name = cred.name
                        self.node.snmpv3_rw_cred_id = cred.id

    def __getitem__(self, item):
        return self._settings[item]

    def __repr__(self):
        return str(self._settings)
