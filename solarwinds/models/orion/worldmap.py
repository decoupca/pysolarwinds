from solarwinds.endpoints.orion.worldmap import Point


class WorldMap(object):
    def __init__(self, swis):
        self.swis = swis

    def point(self, **kwargs):
        return Point(self.swis, **kwargs)
