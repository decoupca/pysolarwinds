from solarwinds.core.model import BaseModel
from solarwinds.endpoints.orion.worldmap import Point


class WorldMap(BaseModel):
    name = 'WorldMap'

    def point(self, **kwargs):
        return Point(self, **kwargs)
