from solarwinds.endpoints.orion.nodes import Node


class Nodes(object):
    def __init__(self, swis):
        self.swis = swis

    def node(self, **kwargs):
        return Node(self.swis, **kwargs)
