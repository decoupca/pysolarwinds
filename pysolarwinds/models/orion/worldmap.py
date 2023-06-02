from pysolarwinds.endpoints.orion.worldmap import WorldMapPoint
from pysolarwinds.models import BaseModel


class WorldMap(BaseModel):
    name = "WorldMap"

    def point(self, **kwargs):
        return WorldMapPoint(self.swis, **kwargs)
