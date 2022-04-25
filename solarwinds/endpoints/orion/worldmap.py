from solarwinds.core.endpoint import Endpoint
from solarwinds.core.exceptions import SWUriNotFound, SWObjectPropertyError

class Point(Endpoint):
    name = 'Point'
    endpoint = 'Orion.WorldMap.Point'
    _required_attrs = ['node', 'instance_id']
    _exclude_args = ['node']
    def __init__(self, swis, node=None, instance_id=None, instance='Orion.Nodes', latitude=None, longitude=None, auto_added=False, street_address=None):
        self.swis = swis
        self.node = node
        self.instance_id = instance_id
        self.instance = instance
        self.latitude = latitude
        self.longitude = longitude
        self.auto_added = auto_added
        self.street_address = street_address

    def _get_uri(self):
        if self.instance_id is not None:
            query = f"SELECT Uri as uri FROM {self.endpoint} WHERE InstanceID = '{self.instance_id}'"
            result = self.query(query)
            if result is None:
                raise SWUriNotFound(f'{self.endpoint}: URI not found for InstanceID="{self.instance_id}"')
            else:
                self.uri = result['uri']

        elif self.node is not None:
            pass

        else:
            raise SWObjectPropertyError(f'Must provide one of these required attributes: '
                                        f'{", ".join(self._required_attrs)}')

    def create(self):
        pass



class PointLabel(Endpoint):
    pass
