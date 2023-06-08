"""Base model."""
from typing import Any

from pysolarwinds.entities import Entity
from pysolarwinds.swis import SWISClient


class BaseModel:
    """Base model."""

    _entity_class = Entity

    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis

    def create(self, **kwargs: Any) -> Entity:
        """Create entity."""
        uri = self.swis.create(self._entity_class.TYPE, **kwargs)[0]["Uri"]
        return self._entity_class(swis=self.swis, uri=uri)
