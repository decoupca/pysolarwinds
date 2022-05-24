from solarwinds.endpoint import Endpoint
from orionsdk import SwisClient

class OrionInterface(Endpoint):
    endpoint = 'Orion.NPM.Interfaces'
    def __init__(self, swis: SwisClient):
        pass

class OrionInterfaceList(object):
    endpoint = 'Orion.NPM.Interfaces'
    def __init__(self, swis: SwisClient) -> None:
        pass