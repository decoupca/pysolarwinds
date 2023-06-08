"""Node settings."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pysolarwinds.exceptions import SWObjectCreationError
from pysolarwinds.logging import get_logger
from pysolarwinds.models.orion.credentials import CredentialsModel

if TYPE_CHECKING:
    from pysolarwinds.entities.orion.nodes import Node

logger = get_logger(__name__)


class NodeSetting:
    """Base node setting class."""

    node_attr = None
    node_attr_value = None

    def __init__(
        self,
        node: Node,
        name: str,
        value: str | int,
        node_setting_id: int | None = None,
    ) -> None:
        """Initialize node setting.

        Args:
            node: Parent node for setting.
            name: Setting name.
            value: Setting value.
            node_setting_id: Node setting ID to retrieve.

        Returns:
            None.

        Raises:
            None.
        """
        self.node = node
        self.swis = node.swis
        self.node_setting_id = node_setting_id
        self.name = name
        self.value = value
        self.build()
        if self.node_attr_value:
            setattr(self.node, self.node_attr, self.node_attr_value)

    def build(self) -> None:
        """Overloaded in subclasses to further build/init setting object."""

    def delete(self) -> None:
        """Delete node setting."""
        return self.node.settings.delete(self)

    def exists(self) -> bool:
        """Whether setting exists."""
        return bool(self.node_setting_id)

    def __repr__(self) -> str:
        return f'<NodeSetting "{self.name}": "{self.value}">'


class SNMPCredentialSetting(NodeSetting):
    """Generic SNMP credential node setting."""

    def build(self) -> None:
        """Build node setting."""
        model = CredentialsModel(swis=self.swis)
        cred = model.get(id=self.value)
        mode = self.name[:2]
        version = int(cred.type[-1:])
        self.node_attr = f"snmpv{version}_{mode.lower()}_cred"
        self.node_attr_value = cred


class NodeSettings:
    """Node settings."""

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

    def __init__(self, node: Node) -> None:
        """Initialize node settings model."""
        self.node = node
        self.swis = node.swis
        self._settings = []
        self.fetch()

    def fetch(self) -> None:
        """Fetch all node settings."""
        self._settings = []
        query = (
            "SELECT SettingName, SettingValue, NodeSettingID "
            f"FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}'"
        )
        settings = self.swis.query(query)
        if settings:
            for setting in settings:
                name = setting["SettingName"]
                value = setting["SettingValue"]
                node_setting_id = setting["NodeSettingID"]
                self._settings.append(self.create(name, value, node_setting_id))

    def create(
        self,
        name: str,
        value: str | int,
        node_setting_id: int | None = None,
    ) -> NodeSetting:
        """Create a new node setting.

        Args:
            name: The setting name.
            value: The setting value.
            node_setting_id: The setting ID.

        Returns:
            A new NodeSetting object.


        Raises:
            None.
        """
        setting_props = self.SETTING_MAP.get(name)
        setting_class = setting_props["class"] if setting_props else NodeSetting
        return setting_class(self.node, name, value, node_setting_id)

    def get(
        self,
        name: str | None = None,
        node_setting_id: int | None = None,
    ) -> NodeSetting | None:
        """Get a node setting by name or ID.

        Args:
            name: Setting name to get.
            node_setting_id: Setting ID to get.
        """
        if name is None and node_setting_id is None:
            msg = "Must provide either `name` or `node_setting_id`."
            raise ValueError(msg)
        if self._settings:
            for setting in self._settings:
                if node_setting_id == setting.node_setting_id:
                    return setting
                if name == setting.name:
                    return setting
            return None
        return None

    def add(self, setting: NodeSetting) -> None:
        """Add a node setting.

        Args:
            setting: `NodeSetting` to add.

        Returns:
            None.

        Raises:
            None.
        """
        statement = (
            "INSERT INTO NodeSettings (NodeID, SettingName, SettingValue) VALUES "
            f"('{setting.node.id}', '{setting.name}', '{setting.value}')"
        )
        self.swis.sql(statement)
        # Raw SQL statements don't return anything, so we need to pull the
        # node_setting_id from a separate query.
        query = (
            "SELECT SettingName, SettingValue, NodeSettingID "
            f"FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}' "
            f"AND SettingName = '{setting.name}'"
        )
        result = self.swis.query(query)
        if result:
            setting.node_setting_id = result[0]["NodeSettingID"]
        else:
            msg = f'Found no setting "{setting.name}" for NodeID {self.node.id} after attempting creation.'
            raise SWObjectCreationError(
                msg,
            )
        self._settings.append(setting)

    def delete(self, setting: NodeSetting) -> None:
        """Delete a node setting."""
        statement = f"DELETE FROM NodeSettings WHERE NodeSettingID = '{setting.node_setting_id}'"
        self.swis.sql(statement)
        self._settings.remove(setting)

    def update(self, old_setting: NodeSetting, new_setting: NodeSetting) -> None:
        """Update a node setting.

        Args:
            old_setting: Old setting to update
            new_setting: New setting to replace `old_setting`

        Returns:
            None.

        Raises:
            None.
        """
        if self.add(new_setting):
            self.delete(old_setting)

    def save(self) -> bool:
        """Save node settings."""
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

                if old_setting:
                    if old_setting.name == setting_name and str(
                        old_setting.value,
                    ) == str(setting_value):
                        logger.debug(
                            f'Setting "{setting_name}" with value "{setting_value}" already set.',
                        )
                    else:
                        new_setting = self.create(
                            name=setting_name,
                            value=setting_value,
                        )
                        self.update(old_setting, new_setting)
                else:
                    new_setting = self.create(name=setting_name, value=setting_value)
                    self.add(new_setting)

    def __getitem__(self, item: NodeSetting) -> NodeSetting:
        return self._settings[item]

    def __repr__(self) -> str:
        return str(self._settings)
