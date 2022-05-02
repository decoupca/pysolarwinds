from solarwinds.model import BaseModel
from solarwinds.endpoints.orion.worldmap import WorldMapPoint


class WorldMap(BaseModel):
    name = "WorldMap"

    def point(self, **kwargs):
        return WorldMapPoint(self.swis, **kwargs)
