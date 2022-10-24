from typing import Union

from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.exceptions import SWObjectNotFound


class OrionNodeSetting(object):

    node_attr = None
    node_attr_value = None

    def __init__(
        self, node, name: str, value: Union[str, int], node_setting_id: int = None
    ):
        self.node = node
        self.swis = node.swis
        self.node_setting_id = node_setting_id
        self.name = name
        self.value = value
        self.build()
        if self.node_attr_value is not None:
            setattr(self.node, self.node_attr, self.node_attr_value)

    def build(self) -> None:
        """overloaded in subclasses to further build/init setting object"""
        pass

    def delete(self) -> bool:
        return self.node.settings.delete(self)

    def exists(self) -> bool:
        return bool(self.node_setting_id)

    def save(self) -> bool:
        # TODO
        pass

    def __repr__(self) -> str:
        return f'<OrionNodeSetting "{self.name}": "{self.value}">'


class SNMPCredentialSetting(OrionNodeSetting):
    def build(self):
        cred = OrionCredential(swis=self.swis, id=self.value)
        mode = self.name[:2]
        version = int(cred.credential_type[-1:])
        self.node_attr = f"snmpv{version}_{mode}_cred"
        self.node_attr_value = cred


class OrionNodeSettings(object):

    CLASS_MAP = {
        "ROSNMPCredentialID": SNMPCredentialSetting,
        "RWSNMPCredentialID": SNMPCredentialSetting,
    }

    def __init__(self, node):
        self.node = node
        self.swis = node.swis
        self._settings = []

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
                setting_class = self.CLASS_MAP.get(name) or OrionNodeSetting
                self._settings.append(
                    setting_class(self.node, name, value, node_setting_id)
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
        pass

    def __getitem__(self, item):
        return self._settings[item]

    def __repr__(self):
        return str(self._settings)
