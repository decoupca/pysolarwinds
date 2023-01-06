from typing import Dict, Optional

from solarwinds.api import API


class OrionPoller:
    _endpoint = "Orion.Pollers"
    _id_attr = "poller_id"
    _name_attr = "poller_type"
    _read_attr_map = {
        "poller_id": "PollerID",
        "poller_type": "PollerType",
        "net_object_id": "NetObjectID",
        "display_name": "DisplayName",
        "description": "Description",
        "enabled": "Enabled",
    }
    _write_attr_map = {
        "enabled": "Enabled",
    }

    def __init__(
        self,
        api: API,
        uri: str,
        net_object_id: Optional[int] = None,
        poller_id: Optional[int] = None,
        poller_type: str = "",
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: bool = True,
    ) -> None:
        self.api = api
        self.uri = uri
        self.net_object_id = net_object_id
        self.poller_id = poller_id
        self.poller_type = poller_type
        self.display_name = display_name
        self.description = description
        self.enabled = enabled

    @property
    def id(self) -> int:
        return getattr(self, self._id_attr)

    @property
    def name(self) -> str:
        return getattr(self, self._name_attr)

    def save(self) -> bool:
        updates = {}
        for attr, prop in self._write_attr_map.items():
            updates.update({prop: getattr(self, attr)})
        self.api.update(self.uri, **updates)
        return True

    def read(self) -> bool:
        data = self.api.read(self.uri)
        for attr, prop in self._read_attr_map.items():
            setattr(self, attr, data.get(prop))
        return True

    def __repr__(self) -> str:
        return (
            f'<OrionPoller: {self.name}: {"Enabled" if self.enabled else "Disabled"}>'
        )

    def __str__(self) -> str:
        return self.name
