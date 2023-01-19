from typing import Dict, List, Optional, Union

from solarwinds.api import API
from solarwinds.exceptions import SWObjectExists
from solarwinds.logging import get_logger

logger = get_logger(__name__)


class OrionPoller:
    _endpoint = "Orion.Pollers"
    _write_attr_map = {
        "enabled": "Enabled",
    }

    def __init__(
        self,
        api: API,
        node,
        data: Optional[Dict] = None,
        uri: Optional[str] = None,
    ) -> None:
        if not uri and not data:
            raise ValueError("must provide URI or data dict")
        self.api = api
        self.node = node
        self.uri = uri
        self._data = data
        if not self.uri:
            self.uri = self._data.get("Uri")
        if not self._data:
            self.read()

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
        logger.debug(f"{self.node}: {self}: updated properties: {updates}")
        return True

    def delete(self) -> bool:
        self.api.delete(self.uri)
        if self.node.pollers.get(self):
            self.node.pollers._pollers.remove(self)
        logger.info(f"{self.node}: {self}: deleted poller")
        return True

    def disable(self) -> bool:
        if not self.enabled:
            logger.debug(f"{self.node}: {self}: poller already disabled")
            return True
        else:
            self.enabled = False
            self.save()
            logger.info(f"{self.node}: {self}: disabled poller")
            return True

    def enable(self) -> bool:
        if self.enabled:
            logger.debug(f"{self.node}: {self}: poller already enabled")
            return True
        else:
            self.enabled = True
            self.save()
            logger.info(f"{self.node}: {self}: enabled poller")
            return True

    def _read(self) -> Dict:
        return self.api.read(self.uri)

    def read(self) -> bool:
        self._data = self._read()
        return True

    def __repr__(self) -> str:
        return (
            f'OrionPoller("{self.name}": {"Enabled" if self.enabled else "Disabled"})'
        )

    def __str__(self) -> str:
        return self.name


class OrionPollers:
    def __init__(self, node, pollers: Optional[List[str]] = None) -> None:
        self.node = node
        self.api = self.node.api
        self._pollers = []
        if self.node.exists():
            self.fetch()
        if pollers:
            for poller in pollers:
                if not self.get(poller):
                    self.add(type=poller, enabled=True)

    @property
    def list(self) -> List:
        return [x.name for x in self._pollers]

    def add(self, poller: str, enabled: bool = True) -> bool:
        if self.get(poller):
            raise SWObjectExists(f"{self.node}: poller already exists: {poller}")

        kwargs = {
            "PollerType": poller,
            "NetObject": f"N:{self.node.id}",
            "NetObjectType": "N",
            "NetObjectID": self.node.id,
            "Enabled": enabled,
        }
        uri = self.api.create("Orion.Pollers", **kwargs)
        data = self.api.read(uri)
        new_poller = OrionPoller(api=self.api, node=self.node, data=data)
        self._pollers.append(new_poller)
        logger.info(
            f"{self.node}: {new_poller}: created new poller "
            f"({'enabled' if enabled else 'disabled'})"
        )
        return True

    def delete(self, poller: Union[OrionPoller, str]) -> bool:
        if isinstance(poller, str):
            poller = self[poller]
        poller.delete()
        return True

    def disable(self, poller: Union[OrionPoller, str]) -> bool:
        if isinstance(poller, str):
            poller = self[poller]
        return poller.disable()

    def enable(self, poller: Union[OrionPoller, str]) -> bool:
        if isinstance(poller, str):
            poller = self[poller]
        return poller.enable()

    def fetch(self) -> None:
        query = (
            f"SELECT PollerID, PollerType, NetObject, NetObjectType, NetObjectID, "
            "Enabled, DisplayName, Description, InstanceType, Uri, InstanceSiteId "
            f"FROM Orion.Pollers WHERE NetObjectID='{self.node.id}'"
        )
        results = self.api.query(query)
        if results:
            pollers = []
            for result in results:
                pollers.append(OrionPoller(api=self.api, node=self.node, data=result))
            self._pollers = pollers

    def get(self, poller: Union[OrionPoller, str]) -> Optional[OrionPoller]:
        for existing_poller in self._pollers:
            if isinstance(poller, str):
                if existing_poller.name == poller:
                    return existing_poller
            if isinstance(poller, OrionPoller):
                if existing_poller == poller:
                    return existing_poller
        return None

    def __getitem__(self, item: Union[str, int]) -> OrionPoller:
        if isinstance(item, int):
            return self._pollers[item]
        elif isinstance(item, str):
            for poller in self._pollers:
                if poller.name == item:
                    return poller
            raise KeyError(f"Poller not found: {item}")

    def __repr__(self) -> str:
        return str(self.list)
