from solarwinds.endpoints.orion.worldmap import Point, PointLabel
from solarwinds.models.orion.nodes import Nodes


class Orion(object):
    def __init__(self, swis):
        self.nodes = Nodes(swis)
