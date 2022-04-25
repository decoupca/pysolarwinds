from urllib.parse import urlencode, urlparse
import re
from solarwinds.core.exceptions import SWObjectPropertyError

class Endpoint(object):
    endpoint = None
    uri = None
    _swdata = None
    # list of attributes required to lookup solarwinds object (OR, not AND)
    _required_attrs = None

    def _update_object(self):
        """ updates local python object's properties with properties read from solarwinds """
        for k, v in self._swdata.items():
            attr = self._camel_to_snake(k)
            try:
                getattr(self, attr)
                setattr(self, attr, v)
            except AttributeError:
                pass

    def _parse_response(self, response):
        if response is not None:
            result = response.get('results')
            if len(result) == 0:
                return None
            elif len(result) == 1:
                return result[0]
            else:
                return result
        else:
            return None

    def _camel_to_snake(self, name):
        """ https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case """
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
    def _get_uri(self):
        """ Get an object's SWIS URI """
        pass

    def _get_swdata(self):
        """ Caches solarwinds data about an object """
        self._swdata = self.swis.read(self.uri)

    def create(self):
        """ Create object """
        pass

    def delete(self):
        """ Delete object """
        if self.exists():
            self.swis.delete(self.uri)
            return True
        else:
            return False

    def exists(self, refresh=False):
        """ Whether or not an object exists """
        if refresh is True:
            self.uri = self._get_uri()
        return bool(self.uri)

    def get(self):
        if self.uri is None:
            self.uri = self._get_uri()
        if self.uri is not None:
            self._swdata = self.swis.read(self.uri)
            self._update_object()
        else:
            raise SWObjectPropertyError('Must provide one of these required attributes: '
                                        f'{", ".join(self._required_attrs)}')

    def query(self, query):
        return self._parse_response(self.swis.query(query))

    def update(self):
        """ Update object in solarwinds with local object's properties """
        pass
