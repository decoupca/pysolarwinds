from typing import Union

from solarwinds.endpoints.orion.credential import OrionCredential


class OrionNodeSetting(object):
    def __init__(self, node, node_setting_id: int, name: str, value: Union[str, int]):
        self.node = node
        self.swis = node.swis
        self.node_setting_id = node_setting_id
        self.name = name
        self.value = value

        if name in ["ROSNMPCredentialID", "RWSNMPCredentialID"]:
            cred = OrionCredential(swis=self.swis, node_id=self.node.id, id=value)
            if name == "ROSNMPCredentialID":
                if cred.credential_type.endswith("SnmpCredentialsV3"):
                    self.node.settings.snmpv3_ro_cred = cred
                    self.node.snmpv3_ro_cred_name = cred.name
                    self.node.snmpv3_ro_cred_id = cred.id
            if name == "RWSNMPCredentialID":
                if cred.credential_type.endswith("SnmpCredentialsV3"):
                    self.node.settings.snmpv3_rw_cred = cred
                    self.node.snmpv3_rw_cred_name = cred.name
                    self.node.snmpv3_rw_cred_id = cred.id


class OrionNodeSettings(object):
    def __init__(self, node):
        self.node = node
        self.swis = node.swis
        self._settings = []

        self.snmpv3_ro_cred = None
        self.snmpv3_rw_cred = None

    def get(self):
        query = (
            "SELECT SettingName, SettingValue, NodeSettingID "
            f"FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}'"
        )
        settings = self.swis.query(query)
        if settings is not None:
            for setting in settings:
                name = setting["SettingName"]
                value = setting["SettingValue"]
                node_setting_id = setting["NodeSettingID"]
                self._settings.append(
                    OrionNodeSetting(self.node, node_setting_id, name, value)
                )

    def add(self, setting: OrionNodeSetting) -> bool:
        statement = (
            "INSERT INTO NodeSettings (NodeID, SettingName, SettingValue) VALUES "
            f"('{setting.node.id}', '{setting.name}', '{setting.value}')"
        )
        self.swis.sql(statement)
        self._settings.append(setting)
        return True

    def delete(self, setting: OrionNodeSetting) -> bool:
        statement = f"DELETE FROM NodeSettings WHERE NodeSettingID = '{setting.node_setting_id}'"
        self.swis.sql(statement)
        self._settings.remove(setting)
        return True

    def __getitem__(self, item):
        return self._settings[item]

    def __repr__(self):
        return str(self._settings)
