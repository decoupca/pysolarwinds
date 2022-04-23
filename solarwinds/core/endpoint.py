from urllib.parse import urlencode, urlparse

class Endpoint(object):
    def __init__(self, parent):
        self.module = parent.module
        self.parent = parent.name
        self.endpoint = f'{self.module}.{self.parent}.{self.name}'
        self.swis = parent.swis
        self.uri = self._build_uri()
        self._cache = self.get()
        self.id = None

    def _build_uri_key(self):
        key = []
        for k, v in self._uri_key.items():
            key.append(f'{k}="{v}"')
        return ','.join(key)

    def _build_uri(self):
        # swis://PTC-WBSOLARW702.ad.moodys.net/Orion/Orion.WorldMap.Point/Instance="Orion.Nodes",InstanceID="799"
        # swis://PTC-WBSOLARW702.ad.moodys.net/Orion/Orion.Nodes/NodeID=1503
        return f'swis://{urlparse(self.swis.url).hostname}/{self.module}/{self.endpoint}/{self._build_uri_key()}'

    def create(self):
        pass

    def delete(self):
        if self.exists():
            self.swis.delete(self.uri)
            return True
        else:
            return False

    def exists(self, refresh=False):
        pass 

    def get(self):
        return self.swis.read(self.uri)

    def read(self):
        pass

    def update(self):
        pass
