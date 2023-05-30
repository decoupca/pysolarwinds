from pysolarwinds.endpoints.orion.worldmap import WorldMapPoint
from pysolarwinds.model import BaseModel


class WorldMap(BaseModel):
    name = "WorldMap"

    def point(self, **kwargs):
        return WorldMapPoint(self.api, **kwargs)
