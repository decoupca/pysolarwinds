from solarwinds.core.endpoint import Endpoint

class Point(Endpoint):
    name = 'Point'
    endpoint = 'Orion.WorldMap.Point'

    def __init__(self, swis, node=None, instance_id=None, instance='Orion.Nodes', latitude=None, longitude=None, auto_added=False, street_address=None):
        self.swis = swis
        self.node = node
        self.instance_id = instance_id
        self.instance = instance
        self.latitude = latitude
        self.longitude = longitude
        self.auto_added = auto_added
        self.street_address = street_address
        self.uri = self._get_uri()

    def _get_uri(self):
        query = f"SELECT Uri FROM {self.endpoint} WHERE InstanceID = '{self.instance_id}'"
        result = self.swis.query(query)
        if result:
            return result['results'][0]['Uri']

    def create(self):
        pass



class PointLabel(Endpoint):
    pass
