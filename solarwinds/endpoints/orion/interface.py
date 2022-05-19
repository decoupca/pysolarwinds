from solarwinds.endpoint import Endpoint
from orionsdk import SwisClient

class OrionNodeInterface(Endpoint):
    endpoint = 'Orion.NPM.Interfaces'
    def __init__(self, swis: SwisClient):
        pass