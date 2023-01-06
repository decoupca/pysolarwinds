from typing import Dict, Optional

from solarwinds.api import API


class OrionPoller:
    _endpoint = "Orion.Pollers"
    _write_attr_map = {
        "enabled": "Enabled",
    }

    def __init__(
        self,
        api: API,
        data: Optional[Dict] = None,
        uri: Optional[str] = None,
    ) -> None:
        self.api = api
        self.uri = uri
        self._data = data
        if not uri and not data:
            raise ValueError("must provide URI or data dict")
        if not self.uri:
            self.uri = self._data.get("Uri")
        if not self._data:
            self._data = self._read()
        self.enabled = self._data.get("Enabled")

    @property
    def id(self) -> int:
        return self.poller_id

    @property
    def display_name(self) -> Optional[str]:
        return self._data.get("DisplayName")

    @property
    def description(self) -> Optional[str]:
        return self._data.get("Description")

    @property
    def poller_id(self) -> int:
        return self._data.get("PollerID")

    @property
    def poller_type(self) -> str:
        return self._data.get("PollerType")

    @property
    def net_object(self) -> str:
        return self._data.get("NetObject")

    @property
    def net_object_type(self) -> str:
        return self._data.get("NetObjectType")

    @property
    def name(self) -> str:
        return self.display_name or self.poller_type

    @property
    def instance_type(self) -> str:
        return self._data.get("InstanceType")

    @property
    def instance_site_id(self) -> bool:
        return self._data.get("InstanceSiteId")

    def save(self) -> bool:
        updates = {}
        for attr, prop in self._write_attr_map.items():
            updates.update({prop: getattr(self, attr)})
        self.api.update(self.uri, **updates)
        return True

    def _read(self) -> Dict:
        return self.api.read(self.uri)

    def read(self) -> bool:
        self._data = self._read()
        return True

    def __repr__(self) -> str:
        return (
            f'<OrionPoller: {self.name}: {"Enabled" if self.enabled else "Disabled"}>'
        )

    def __str__(self) -> str:
        return self.name
