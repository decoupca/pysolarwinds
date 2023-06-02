from typing import Optional, Union

from pysolarwinds.endpoint import NewEndpoint
from pysolarwinds.exceptions import SWObjectExists
from pysolarwinds.list import BaseList
from pysolarwinds.logging import get_logger
from pysolarwinds.swis import SWISClient

logger = get_logger(__name__)


class OrionPoller(NewEndpoint):
    _entity_type = "Orion.Pollers"
    _uri_template = "swis://{}/Orion/Orion.Pollers/PollerID={}"
    _write_attr_map = {
        "is_enabled": "Enabled",
    }

    def __init__(
        self,
        swis: SWISClient,
        node,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        super().__init__(swis=swis, id=id, uri=uri, data=data)
        self.node = node
        self.is_enabled: bool = self.data["Enabled"]

    @property
    def _id(self) -> int:
        return self.poller_id

    @property
    def display_name(self) -> str:
        return self.data["DisplayName"]

    @property
    def poller_id(self) -> int:
        return self.data["PollerID"]

    @property
    def poller_type(self) -> str:
        return self.data.get("PollerType", "")

    @property
    def net_object(self) -> str:
        return self.data.get("NetObject", "")

    @property
    def net_object_type(self) -> str:
        return self.data.get("NetObjectType", "")

    @property
    def name(self) -> str:
        return self.display_name or self.poller_type

    @property
    def instance_type(self) -> str:
        return self.data.get("InstanceType", "")

    def delete(self) -> None:
        self.swis.delete(self.uri)
        if self.node.pollers.get(self):
            self.node.pollers.items.remove(self)
        logger.info(f"{self.node}: {self}: deleted poller")

    def disable(self) -> None:
        if not self.is_enabled:
            logger.debug(f"{self.node}: {self}: poller already disabled")
        else:
            self.is_enabled = False
            self.save()
            logger.info(f"{self.node}: {self}: disabled poller")

    def enable(self) -> None:
        if self.is_enabled:
            logger.debug(f"{self.node}: {self}: poller already enabled")
        else:
            self.is_enabled = True
            self.save()
            logger.info(f"{self.node}: {self}: enabled poller")

    def __repr__(self) -> str:
        return f"OrionPoller(id={self.id})"


class OrionPollers(BaseList):
    _item_class = OrionPoller

    def __init__(self, node) -> None:
        self.node = node
        self.swis = self.node.swis
        self.items = []

    @property
    def names(self) -> list:
        return [x.name for x in self.items]

    def add(self, pollers: Union[list[str], str], enabled: bool = True) -> bool:
        if isinstance(pollers, str):
            pollers = [pollers]
        for poller in pollers:
            if self.get(poller):
                raise SWObjectExists(f"{self.node}: poller already exists: {poller}")

            kwargs = {
                "PollerType": poller,
                "NetObject": f"N:{self.node.id}",
                "NetObjectType": "N",
                "NetObjectID": self.node.id,
                "Enabled": enabled,
            }
            uri = self.swis.create("Orion.Pollers", **kwargs)
            data = self.swis.read(uri)
            new_poller = OrionPoller(swis=self.swis, node=self.node, data=data)
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
            self.swis.delete([x.uri for x in self.items])
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
        if results := self.swis.query(query):
            pollers = [
                OrionPoller(swis=self.swis, node=self.node, data=x) for x in results
            ]
            self.items = pollers

    def __repr__(self) -> str:
        if not self.items:
            self.fetch()
        return super().__repr__()