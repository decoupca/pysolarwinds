from solarwinds.endpoints.orion.worldmap import WorldMapPoint
from solarwinds.model import BaseModel


class WorldMap(BaseModel):
    name = "WorldMap"

    def point(self, **kwargs):
        return WorldMapPoint(self.api, **kwargs)
