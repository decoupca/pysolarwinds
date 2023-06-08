from typing import Any, Union


class BaseList:
    _item_class = None

    def __init__(self, node) -> None:
        self.node = node
        self.swis = self.node.swis
        self.items = []

    def fetch(self) -> None:
        pass

    def get(self, item: Any) -> Any:
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
            for item in self.items:
                if item.name == item:
                    return item
            msg = f"Item not found: {item}"
            raise KeyError(msg)
        return None

    def __repr__(self) -> str:
        if not self.items:
            self.fetch()
        return str(self.items)
