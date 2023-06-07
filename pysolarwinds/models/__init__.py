class BaseModel:
    _entity_class = None

    def __init__(self, swis):
        self.swis = swis

    def create(self, **kwargs) -> _entity_class:
        uri = self.swis.create(self._entity_class.TYPE, **kwargs)
        return self._entity_class(swis=self.swis, uri=uri)
