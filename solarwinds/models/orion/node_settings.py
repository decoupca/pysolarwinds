from typing import Union

from solarwinds.endpoint import Endpoint
from solarwinds.endpoints.orion.credential import OrionCredential
from solarwinds.exceptions import SWObjectCreationError, SWObjectNotFound
from solarwinds.logging import get_logger

logger = get_logger(__name__)


class OrionNodeSetting:

    node_attr = None
    node_attr_value = None

    def __init__(
        self, node, name: str, value: Union[str, int], node_setting_id: int = None
    ) -> None:
        self.node = node
        self.api = node.api
        self.node_setting_id = node_setting_id
        self.name = name
        self.value = value
        self.build()
        if self.node_attr_value:
            setattr(self.node, self.node_attr, self.node_attr_value)

    def build(self) -> None:
        """overloaded in subclasses to further build/init setting object"""
        pass

    def delete(self) -> bool:
        return self.node.settings.delete(self)

    def exists(self) -> bool:
        return bool(self.node_setting_id)

    def __repr__(self) -> str:
        return f'<OrionNodeSetting "{self.name}": "{self.value}">'


class SNMPCredentialSetting(OrionNodeSetting):
    def build(self) -> None:
        cred = OrionCredential(api=self.api, id=self.value)
        mode = self.name[:2]
        version = int(cred.credential_type[-1:])
        self.node_attr = f"snmpv{version}_{mode.lower()}_cred"
        self.node_attr_value = cred


class OrionNodeSettings(object):

    SETTING_MAP = {
        "ROSNMPCredentialID": {
            "class": SNMPCredentialSetting,
            "node_attr": "snmpv3_ro_cred",
            "setting_value_attr": "id",
        },
        "RWSNMPCredentialID": {
            "class": SNMPCredentialSetting,
            "node_attr": "snmpv3_rw_cred",
            "setting_value_attr": "id",
        },
    }

    def __init__(self, node):
        self.node = node
        self.api = node.api
        self._settings = []

    def fetch(self) -> None:
        self._settings = []
        query = (
            "SELECT SettingName, SettingValue, NodeSettingID "
            f"FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}'"
        )
        settings = self.api.query(query)
        if settings:
            for setting in settings:
                name = setting["SettingName"]
                value = setting["SettingValue"]
                node_setting_id = setting["NodeSettingID"]
                self._settings.append(self.create(name, value, node_setting_id))

    def create(self, name: str, value, node_setting_id=None) -> OrionNodeSetting:
        setting_props = self.SETTING_MAP.get(name)
        if setting_props:
            setting_class = setting_props["class"]
        else:
            setting_class = OrionNodeSetting
        return setting_class(self.node, name, value, node_setting_id)

    def get(
        self, name: str = None, node_setting_id: int = None
    ) -> Union[OrionNodeSetting, None]:
        if name is None and node_setting_id is None:
            raise ValueError("must provide either setting `name` or `node_setting_id`")
        if self._settings:
            for setting in self._settings:
                if node_setting_id is not None:
                    if node_setting_id == setting.node_setting_id:
                        return setting
                if name == setting.name:
                    return setting

    def add(self, setting: OrionNodeSetting) -> bool:
        statement = (
            "INSERT INTO NodeSettings (NodeID, SettingName, SettingValue) VALUES "
            f"('{setting.node.id}', '{setting.name}', '{setting.value}')"
        )
        self.api.sql(statement)
        # raw SQL statements don't return anything, so we need to pull the
        # node_setting_id from a separate query
        query = (
            "SELECT SettingName, SettingValue, NodeSettingID "
            f"FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}' "
            f"AND SettingName = '{setting.name}'"
        )
        result = self.api.query(query)
        if result:
            setting.node_setting_id = result[0]["NodeSettingID"]
        else:
            raise SWObjectCreationError(
                f'found no setting "{setting.name}" '
                f"for NodeID {self.node.id} after attempting creation"
            )
        self._settings.append(setting)
        return True

    def delete(self, setting: OrionNodeSetting) -> bool:
        statement = f"DELETE FROM NodeSettings WHERE NodeSettingID = '{setting.node_setting_id}'"
        self.api.sql(statement)
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
        for setting_name, setting_props in self.SETTING_MAP.items():
            node_attr = setting_props["node_attr"]
            setting_value_attr = setting_props["setting_value_attr"]
            node_attr_value = getattr(self.node, node_attr)
            old_setting = self.get(name=setting_name)
            if node_attr_value is None:
                if old_setting:
                    old_setting.delete()
            else:
                setting_value = getattr(node_attr_value, setting_value_attr)
                if isinstance(node_attr_value, Endpoint):
                    if node_attr_value.exists() is False:
                        raise SWObjectNotFound(
                            f'{node_attr_value.endpoint} "{node_attr_value.name}" does not exist'
                        )

                if old_setting:
                    if old_setting.name == setting_name and str(
                        old_setting.value
                    ) == str(setting_value):
                        logger.debug(
                            f'setting "{setting_name}" with value "{setting_value}" already set'
                        )
                    else:
                        new_setting = self.create(
                            name=setting_name, value=setting_value
                        )
                        self.update(old_setting, new_setting)
                else:
                    new_setting = self.create(name=setting_name, value=setting_value)
                    self.add(new_setting)

    def __getitem__(self, item):
        return self._settings[item]

    def __repr__(self):
        return str(self._settings)
