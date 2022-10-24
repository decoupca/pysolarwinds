from typing import Union

from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.exceptions import SWObjectNotFound


class OrionNodeSetting(object):
    def __init__(
        self, node, name: str, value: Union[str, int], node_setting_id: int = None
    ):
        self.node = node
        self.swis = node.swis
        self.node_setting_id = node_setting_id
        self.name = name
        self.value = value

        if name in ["ROSNMPCredentialID", "RWSNMPCredentialID"]:
            cred = OrionCredential(swis=self.swis, id=value)
            if name == "ROSNMPCredentialID":
                if cred.credential_type.endswith("SnmpCredentialsV3"):
                    self.node.settings.snmpv3_ro_cred = cred
            if name == "RWSNMPCredentialID":
                if cred.credential_type.endswith("SnmpCredentialsV3"):
                    self.node.settings.snmpv3_rw_cred = cred

    def delete(self) -> bool:
        return self.node.settings.delete(self)

    def __repr__(self) -> str:
        return f'<OrionNodeSetting "{self.name}={self.value}"'


class OrionNodeSettings(object):
    def __init__(self, node):
        self.node = node
        self.swis = node.swis
        self._settings = []

        self.snmpv3_ro_cred = None
        self.snmpv3_rw_cred = None

    def fetch(self):
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
                    OrionNodeSetting(self.node, name, value, node_setting_id)
                )

    def get(
        self, name: str = None, node_setting_id: int = None
    ) -> Union[OrionNodeSetting, None]:
        if name is None and node_setting_id is None:
            raise ValueError("must provide either setting `name` or `node_setting_id`")
        if self._settings:
            for setting in self._settings:
                if name == setting.name or node_setting_id == setting.node_setting_id:
                    return setting

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

    def update(
        self, old_setting: OrionNodeSetting, new_setting: OrionNodeSetting
    ) -> bool:
        if self.add(new_setting):
            self.delete(old_setting)
            return True
        return False

    def save(self) -> bool:
        if self.snmpv3_ro_cred is None:
            old_setting = self.get(name="ROSNMPCredentialID")
            if old_setting:
                self.delete(old_setting)

        if self.snmpv3_ro_cred is not None:
            if self.snmpv3_ro_cred.exists():
                new_setting = OrionNodeSetting(
                    node=self.node,
                    name="ROSNMPCredentialID",
                    value=self.snmpv3_ro_cred.id,
                )
                old_setting = self.get(name="ROSNMPCredentialID")
                if old_setting:
                    self.update(old_setting, new_setting)
                else:
                    self.add(new_setting)
            else:
                raise SWObjectNotFound(
                    f'Credential "{self.snmpv3_ro_cred.name}" does not exist'
                )

    def __getitem__(self, item):
        return self._settings[item]

    def __repr__(self):
        return str(self._settings)
