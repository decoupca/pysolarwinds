from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from pysolarwinds.entities import Entity
from pysolarwinds.exceptions import SWObjectExistsError, SWObjectNotFoundError
from pysolarwinds.list import BaseList
from pysolarwinds.logging import get_logger
from pysolarwinds.queries.orion.pollers import QUERY, TABLE
from pysolarwinds.swis import SWISClient

if TYPE_CHECKING:
    from pysolarwinds.entities.orion.nodes import Node

logger = get_logger(__name__)


class Poller(Entity):
    TYPE = "Orion.Pollers"
    URI_TEMPLATE = "swis://{}/Orion/Orion.Pollers/PollerID={}"
    WRITE_ATTR_MAP = {
        "is_enabled": "Enabled",
    }

    def __init__(
        self,
        swis: SWISClient,
        node: Node,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
        poller_type: Optional[str] = None,
    ) -> None:
        self.node = node
        super().__init__(swis=swis, id=id, uri=uri, data=data, poller_type=poller_type)
        self.poller_type = poller_type or self.data.get("PollerType", "")
        self.is_enabled: bool = self.data["Enabled"]

    def _get_data(self) -> Optional[dict]:
        if self.poller_type:
            query = QUERY.where(TABLE.PollerType == self.poller_type)
            if results := self.swis.query(str(query)):
                return results[0]
            else:
                msg = f'No poller "{self.poller_type}" on node ID {self.node.id} found.'
                raise SWObjectNotFoundError(
                    msg,
                )
        return None

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
        return f"Poller(node={self.node.__repr__()}, poller_type='{self.poller_type}')"


class PollerList(BaseList):
    _item_class = Poller

    def __init__(self, node: Node) -> None:
        self.node = node
        self.swis = self.node.swis
        self.items = []

    @property
    def names(self) -> list:
        return [x.name for x in self.items]

    def add(self, pollers: Union[list[str], str], *, enabled: bool) -> None:
        if isinstance(pollers, str):
            pollers = [pollers]
        for poller in pollers:
            if self.get(poller):
                msg = f"{self.node}: poller already exists: {poller}"
                raise SWObjectExistsError(msg)

            kwargs = {
                "PollerType": poller,
                "NetObject": f"N:{self.node.id}",
                "NetObjectType": "N",
                "NetObjectID": self.node.id,
                "Enabled": enabled,
            }
            uri = self.swis.create("Orion.Pollers", **kwargs)
            data = self.swis.read(uri)
            new_poller = Poller(swis=self.swis, node=self.node, data=data)
            self.items.append(new_poller)
            logger.info(
                f"{new_poller}: created new poller "
                f"({'enabled' if enabled else 'disabled'})",
            )

    def delete(self, poller: Union[Poller, str]) -> None:
        if isinstance(poller, str):
            poller = self[poller]
        poller.delete()

    def delete_all(self) -> None:
        self.fetch()
        pollers = self.items
        if pollers:
            self.swis.delete([x.uri for x in self.items])
            self.items = []
            logger.info(f"Deleted all pollers ({len(pollers)}).")
        else:
            logger.debug("No pollers to delete; doing nothing.")

    def disable(self, poller: Union[Poller, str]) -> None:
        if isinstance(poller, str):
            poller = self[poller]
        poller.disable()

    def disable_all(self) -> None:
        for poller in self.items:
            if poller.is_enabled:
                poller.disable()

    def enable(self, poller: Union[Poller, str]) -> None:
        if isinstance(poller, str):
            poller = self[poller]
        return poller.enable()

    def enable_all(self) -> None:
        for poller in self.items:
            if not poller.is_enabled:
                poller.disable()

    def fetch(self) -> None:
        query = (
            f"SELECT PollerID, PollerType, NetObject, NetObjectType, NetObjectID, "
            "Enabled, DisplayName, Description, InstanceType, Uri, InstanceSiteId "
            f"FROM Orion.Pollers WHERE NetObjectID='{self.node.id}'"
        )
        if results := self.swis.query(query):
            pollers = [Poller(swis=self.swis, node=self.node, data=x) for x in results]
            self.items = pollers

    def __repr__(self) -> str:
        if not self.items:
            self.fetch()
        return super().__repr__()
