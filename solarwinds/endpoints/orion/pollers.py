from typing import Dict, List, Optional, Union

from solarwinds.api import API
from solarwinds.endpoint import NewEndpoint
from solarwinds.exceptions import SWObjectExists
from solarwinds.list import BaseList
from solarwinds.logging import get_logger

logger = get_logger(__name__)


class OrionPoller(NewEndpoint):
    _entity_type = "Orion.Pollers"
    _write_attr_map = {
        "is_enabled": "Enabled",
    }

    def __init__(
        self,
        api: API,
        node,
        data: Optional[Dict] = None,
        uri: Optional[str] = None,
    ) -> None:
        super().__init__(api=api, data=data, uri=uri)
        self.node = node
        self.is_enabled = self.data.get("Enabled")

    @property
    def id(self) -> int:
        return self.poller_id

    @property
    def display_name(self) -> Optional[str]:
        return self.data.get("DisplayName")

    @property
    def description(self) -> Optional[str]:
        return self.data.get("Description")

    @property
    def poller_id(self) -> int:
        return self.data.get("PollerID")

    @property
    def poller_type(self) -> str:
        return self.data.get("PollerType")

    @property
    def net_object(self) -> str:
        return self.data.get("NetObject")

    @property
    def net_object_type(self) -> str:
        return self.data.get("NetObjectType")

    @property
    def name(self) -> str:
        return self.display_name or self.poller_type

    @property
    def instance_type(self) -> str:
        return self.data.get("InstanceType")

    @property
    def instance_site_id(self) -> bool:
        return self.data.get("InstanceSiteId")

    def delete(self) -> bool:
        self.api.delete(self.uri)
        self.node.pollers.items.remove(self)
        logger.info(f"{self.node}: {self}: deleted poller")
        return True

    def disable(self) -> bool:
        if not self.is_enabled:
            logger.debug(f"{self.node}: {self}: poller already disabled")
            return True
        else:
            self.is_enabled = False
            self.save()
            logger.info(f"{self.node}: {self}: disabled poller")
            return True

    def enable(self) -> bool:
        if self.is_enabled:
            logger.debug(f"{self.node}: {self}: poller already enabled")
            return True
        else:
            self.is_enabled = True
            self.save()
            logger.info(f"{self.node}: {self}: enabled poller")
            return True

    def __repr__(self) -> str:
        return f'OrionPoller("{self.name}": {"Enabled" if self.is_enabled else "Disabled"})'


class OrionPollers(BaseList):
    _item_class = OrionPoller

    def __init__(self, node, enabled_pollers: Optional[List[str]] = None) -> None:
        self.node = node
        self.api = self.node.api
        self._enabled_pollers = enabled_pollers
        self.items = []
        if self.node.exists():
            self.fetch()
            if self._enabled_pollers:
                for poller in self._enabled_pollers:
                    if not self.get(poller):
                        self.add(poller=poller, enabled=True)
                    else:
                        self.get(poller).enable()

    @property
    def list(self) -> List:
        return [x.name for x in self.items]

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
        self.items.append(new_poller)
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

    def delete_all(self) -> bool:
        pollers = self.items
        if pollers:
            self.api.delete([x.uri for x in self.items])
            self.items = []
            logger.info(f"{self.node}: Deleted all {len(pollers)} pollers")
        else:
            logger.debug(f"{self.node}: No pollers to delete, doing nothing")
        return True

    def disable(self, poller: Union[OrionPoller, str]) -> bool:
        if isinstance(poller, str):
            poller = self[poller]
        return poller.disable()

    def disable_all(self) -> bool:
        for poller in self.items:
            if poller.is_enabled:
                poller.disable()
        return True

    def enable(self, poller: Union[OrionPoller, str]) -> bool:
        if isinstance(poller, str):
            poller = self[poller]
        return poller.enable()

    def enable_all(self) -> bool:
        for poller in self.items:
            if not poller.is_enabled:
                poller.disable()
        return True

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
            self.items = pollers
