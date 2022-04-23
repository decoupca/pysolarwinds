class Point(object):
    def __init__(self, swis, instance_id, instance='Orion.Nodes', latitude=None, longitude=None, auto_added=False, street_address=None):
        self.swis = swis
        self.instance_id = instance_id
        self.instance = instance
        self.latitude = latitude
        self.longitude = longitude
        self.auto_added = auto_added
        self.street_address = street_address
        self.uri = None

    def create(self):
        pass

    def exists(self, refresh=False):
        return bool(self.get_uri(refresh=refresh))

    def get_uri(self, refresh=False):
        if self.uri is None or refresh is True:
            query = f"SELECT Uri FROM Orion.WorldMap.Point WHERE InstanceID = '{self.instance_id}'"
            results = self.swis.query(query)
            if results is not None:
                self.uri = results['results'][0]['Uri']
        return self.uri

    def details(self):
        return self.swis.read(self.get_uri())


class PointLabel(object):
    pass
