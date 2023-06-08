"""Base list."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from pysolarwinds.entities import Entity

if TYPE_CHECKING:
    from pysolarwinds.entities.orion.nodes import Node


class BaseList:
    """Base list."""

    _item_class = Entity

    def __init__(self, node: Node) -> None:
        self.node = node
        self.swis = self.node.swis
        self.items = []

    def fetch(self) -> None:
        """Fetch all items."""

    def get(self, item: Any) -> Any:
        """Gets an item from list."""
        for existing_item in self.items:
            if isinstance(item, str) and existing_item.name == item:
                return existing_item
            if isinstance(item, self._item_class) and existing_item == item:
                return existing_item
        return None

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, item: Union[str, int]) -> Any:
        if isinstance(item, int):
            return self.items[item]
        elif isinstance(item, str):
            for i in self.items:
                if i.name == item:
                    return item
            msg = f"Item not found: {item}"
            raise KeyError(msg)
        return None

    def __repr__(self) -> str:
        if not self.items:
            self.fetch()
        return str(self.items)
