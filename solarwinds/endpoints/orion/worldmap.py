from solarwinds.core.endpoint import Endpoint

class Point(Endpoint):
    def __init__(self, parent, instance_id, instance='Orion.Nodes', latitude=None, longitude=None, auto_added=False, street_address=None):
        self.name = 'Point'
        self.instance_id = instance_id
        self.instance = instance
        self.latitude = latitude
        self.longitude = longitude
        self.auto_added = auto_added
        self.street_address = street_address
        self._uri_key = {'Instance': self.instance, 'InstanceID': instance_id}
        super().__init__(parent)

    def create(self):
        pass



class PointLabel(Endpoint):
    pass
