from typing import Dict

from solarwinds.api import API


class OrionPoller:
    _endpoint = "Orion.Pollers"
    _id_attr = "poller_id"
    _name_attr = "poller_type"
    _attr_map = {
        "enabled": "Enabled",
    }

    def __init__(
        self,
        api: API,
        uri: str,
        net_object_id: int,
        poller_id: int,
        poller_type: str,
        enabled: bool,
    ) -> None:
        self.api = api
        self.uri = uri
        self.net_object_id = net_object_id
        self.poller_id = poller_id
        self.poller_type = poller_type
        self.enabled = enabled

    @property
    def id(self) -> int:
        return getattr(self, self._id_attr)

    @property
    def name(self) -> str:
        return getattr(self, self._name_attr)

    def save(self) -> bool:
        updates = {}
        for attr, prop in self._attr_map.items():
            updates.update({prop: getattr(self, attr)})
        self.api.update(self.uri, **updates)
        return True

    def read(self) -> Dict:
        return self.api.read(self.uri)

    def __repr__(self) -> str:
        return (
            f'<OrionPoller: {self.name}: {"Enabled" if self.enabled else "Disabled"}>'
        )

    def __str__(self) -> str:
        return self.name
