import re

from pysolarwinds.entities import Entity
from pysolarwinds.swis import SWISClient


class CustomProperties:
    EXCLUDE_ATTRS = (
        "DisplayName",
        "Description",
        "InstanceType",
        "InstanceSiteId",
        "Uri",
    )

    def __init__(self, swis: SWISClient, entity: Entity) -> None:
        self.swis: SWISClient = swis
        self.entity: Entity = entity
        self.data: dict = {}
        self.props: dict = {}
        self.read()
        for k, v in self.data.items():
            if k not in self.EXCLUDE_ATTRS and not re.match(
                r"^.*ID$",
                k,
            ):  # Exclude all keys ending in "ID"
                self.props[k] = v
                setattr(self, k, v)

    @property
    def uri(self) -> str:
        return f"{self.entity.uri}/CustomProperties"

    def read(self) -> None:
        self.data = self.swis.read(self.uri)

    def save(self) -> None:
        changed = False
        for k in self.props:
            if self.props[k] != getattr(self, k):
                changed = True
                self.props[k] = getattr(self, k)
                self.data[k] = getattr(self, k)

        if changed:
            self.swis.update(self.uri, **self.props)

    def __repr__(self) -> str:
        return str(self.props)
