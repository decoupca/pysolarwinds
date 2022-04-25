import inspect
import re
from urllib.parse import urlencode, urlparse

from solarwinds.core.exceptions import SWObjectPropertyError, SWUriNotFound


class Endpoint(object):
    endpoint = None
    uri = None
    _swdata = None
    _localdata = None
    _updates = None
    # list of attributes required to lookup solarwinds object (OR, not AND)
    _required_attrs = None
    # args to exclude when serializing object to push to solarwinds
    _exclude_args = []
    _attr_map = None

    def _build_attr_map(self):
        """builds a map of local attributes to solarwinds properties"""
        attr_map = {}
        for sw_k, sw_v in self._swdata.items():
            local_attr = self._camel_to_snake(sw_k)
            try:
                getattr(self, local_attr)
                attr_map[local_attr] = sw_k
            except AttributeError:
                pass
        if attr_map:
            self._attr_map = attr_map

    def _update_object(self, overwrite=False):
        """updates local python object's properties with properties read from solarwinds
        if overwrite=False, will not update any attributes that are already set
        """
        for local_attr, sw_attr in self._attr_map.items():
            local_v = getattr(self, local_attr)
            if local_v is None or overwrite is True:
                sw_v = self._swdata[sw_attr]
                setattr(self, local_attr, sw_v)

    def _parse_response(self, response):
        if response is not None:
            result = response.get("results")
            if len(result) == 0:
                return None
            elif len(result) == 1:
                return result[0]
            else:
                return result
        else:
            return None

    def _serialize(self):
        serialized = {}
        args = inspect.getfullargspec(self.__init__)[0]
        exclude_args = ["self", "swis"]
        exclude_args.extend(self._exclude_args)
        for arg in args:
            if arg not in exclude_args:
                value = getattr(self, arg)
                # store args without underscores so they match
                # solarwinds argument names
                arg = arg.replace("_", "")
                serialized[arg] = value
        self._localdata = serialized

    def _diff(self):
        updates = {}
        self._serialize()
        if self._swdata is None:
            self._get_swdata()
        for k, v in self._swdata.items():
            k = k.lower()
            local_v = self._localdata.get(k)
            if local_v:
                if local_v != v:
                    updates[k] = self._localdata[k]
        if updates:
            self._updates = updates

    def _camel_to_snake(self, name):
        """https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case"""
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    def _get_uri(self):
        """Get an object's SWIS URI"""
        pass

    def _get_swdata(self, refresh=False):
        """Caches solarwinds data about an object"""
        if self._swdata is None or refresh is True:
            self._swdata = self._sanitize_swdata(self.swis.read(self.uri))
            self._build_attr_map()

    def _sanitize_swdata(self, swdata):
        for k, v in swdata.items():
            if isinstance(v, str):
                if re.match(r"^\d+$", v):
                    swdata[k] = int(v)
        return swdata

    def create(self):
        """Create object"""
        if self.exists():
            return False
        else:
            self._serialize()
            if self._localdata is None:
                raise SWObjectPropertyError(f"Can't create object without properties.")
            else:
                self.uri = self.swis.create(self.endpoint, **self._localdata)
                return True

    def delete(self):
        """Delete object"""
        if self.exists():
            self.swis.delete(self.uri)
            self.uri = None
            return True
        else:
            return False

    def exists(self, refresh=False):
        """Whether or not an object exists"""
        if self.uri is not None:
            return True
        if self.uri is None or refresh is True:
            try:
                self._get_uri()
                return True
            except SWUriNotFound:
                return False

    def get(self, refresh=False, overwrite=False):
        """Gets object data from solarwinds and updates local object attributes"""
        if self.exists(refresh=refresh):
            self._get_swdata(refresh=refresh)
            self._update_object(overwrite=overwrite)

    def query(self, query):
        return self._parse_response(self.swis.query(query))

    def update(self):
        """Update object in solarwinds with local object's properties"""
        if self.exists():
            if self._updates is None:
                self._diff()
            if self._updates is not None:
                self.swis.update(self.uri, **self._updates)
                self.get(refresh=True)
                self._updates = None
                return True
            else:
                return False
        else:
            return self.create()
