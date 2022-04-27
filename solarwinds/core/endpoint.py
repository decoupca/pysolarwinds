import inspect
import re
from logging import getLogger

from solarwinds.core.exceptions import SWObjectPropertyError, SWUriNotFound
from solarwinds.utils import camel_to_snake, parse_response, sanitize_swdata


class Endpoint(object):
    endpoint = None
    uri = None
    id = None
    _swdata = None
    _localdata = None
    _changes = None
    # list of attributes required to lookup solarwinds object (OR, not AND)
    _required_attrs = None
    _keys = None
    # attributes to exclude when serializing object to push to solarwinds
    _exclude_attrs = []
    _exclude_custom_props = ['NodeID', 'InstanceType', 'Uri', 'InstanceSiteId']
    _attr_map = None
    _child_objects = None

    def _init_child_objects(self):
        if self._child_objects is not None:
            for child_object, props in self._child_objects.items():
                init_args = props['init_args']
                local_attr = props['local_attr']
                attr_map = props['attr_map']
                child_args = {}
                for child_arg, parent_arg in init_args.items():
                    parent_v = getattr(self, parent_arg)
                    if parent_v is None:
                        raise SWObjectPropertyError(f"Can't init child object {child_object}, parent arg {parent_arg} is None")
                    else:
                        child_args[child_arg] = parent_arg
                setattr(self, local_attr, child_object(self.swis, **child_args))

    def _get_logger(self):
        self.logger = getLogger(self.endpoint)

    def _build_attr_map(self):
        """builds a map of local attributes to solarwinds properties"""
        attr_map = {}
        for sw_k, sw_v in self._swdata["properties"].items():
            local_attr = camel_to_snake(sw_k)
            try:
                getattr(self, local_attr)
                attr_map[local_attr] = sw_k
            except AttributeError:
                pass
        if attr_map:
            self._attr_map = attr_map

    def _update_object(self, overwrite=False):
        """changes local python object's properties with properties read from solarwinds
        if overwrite=False, will not update any attributes that are already set
        """
        for local_attr, sw_attr in self._attr_map.items():
            local_v = getattr(self, local_attr)
            if local_v is None or overwrite is True:
                sw_v = self._swdata["properties"][sw_attr]
                setattr(self, local_attr, sw_v)
        if self._swdata.get('custom_properties') is not None:
            cprops = {}
            for k, v in self._swdata['custom_properties'].items():
                if k not in self._exclude_custom_props:
                    cprops[k] = v
            if len(cprops) > 0:
                self.custom_properties = cprops

    def _serialize(self):
        serialized = {"properties": {}, "custom_properties": None}
        args = inspect.getfullargspec(self.__init__)[0]
        exclude_attrs = ["self", "swis", "custom_properties"]
        exclude_attrs.extend(self._exclude_attrs)
        for arg in args:
            if arg not in exclude_attrs:
                value = getattr(self, arg)
                # store args without underscores so they match
                # solarwinds argument names
                arg = arg.replace("_", "")
                serialized["properties"][arg] = value
        if self.custom_properties is not None:
            serialized["custom_properties"] = self.custom_properties
        self._localdata = serialized

    def _diff_properties(self):
        changes = {}
        self._serialize()
        if self._swdata is None:
            self._get_swdata()
        for k, sw_v in self._swdata["properties"].items():
            k = k.lower()
            if self._localdata["properties"] is not None:
                local_v = self._localdata["properties"].get(k)
                if local_v:
                    if local_v != sw_v:
                        changes[k] = local_v
        if len(changes) > 0:
            return changes

    def _diff_custom_properties(self):
        changes = {}
        self._serialize()
        if self._swdata is None:
            self._get_swdata()
        for k, local_v in self._localdata["custom_properties"].items():
            if k not in self._swdata["custom_properties"].keys():
                changes[k] = local_v
            sw_v = self._swdata["custom_properties"].get(k)
            if sw_v != local_v:
                changes[k] = local_v
        if len(changes) > 0:
            return changes

    def _diff(self):
        changes = {
            "properties": self._diff_properties(),
            "custom_properties": self._diff_custom_properties(),
        }
        if (
            changes["properties"] is not None
            or changes["custom_properties"] is not None
        ):
            self._changes = changes

    def _get_id(self):
        self.id = int(re.search(r"(\d+)$", self.uri).group(0))
        self.logger.debug(f"get_id(): got id: {self.id}")

    def _get_uri(self):
        """Get an object's SWIS URI"""
        queries = []
        for key in self._keys:
            value = getattr(self, key)
            if value is not None:
                sw_key = key.replace('_', '')
                queries.append(
                    f"SELECT Uri as uri FROM {self.endpoint} WHERE {sw_key} = '{value}'"
                )
        if queries:
            query_lines = "\n".join(queries)
            self.logger.debug(f"Found queries:\n{query_lines}")
            for query in queries:
                result = self.query(query)
                if result:
                    self.uri = result["uri"]
                    return True
            raise SWUriNotFound(
                f"No results found for any of these queries:\n{query_lines}"
            )
        else:
            key_props = ", ".join(self._keys)
            raise SWUriNotFound(
                f"Must provide a value for at least one key property: {key_props}"
            )

    def _get_swdata(self, refresh=False):
        """Caches solarwinds data about an object"""
        if self._swdata is None or refresh is True:
            self._swdata = {}
            self._swdata["properties"] = sanitize_swdata(self.swis.read(self.uri))
            try:
                getattr(self, 'custom_properties')
                self._swdata["custom_properties"] = sanitize_swdata(
                    self.swis.read(f"{self.uri}/CustomProperties")
                )
            except AttributeError:
                pass
            self._build_attr_map()

    def create(self):
        """Create object"""
        if self.exists():
            return False
        else:
            self._serialize()
            if self._localdata is None:
                raise SWObjectPropertyError("Can't create object without properties.")
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
            self._init_child_objects()

    def query(self, query):
        return parse_response(self.swis.query(query))

    def update(self):
        """Update object in solarwinds with local object's properties"""
        if self.exists():
            if self._changes is None:
                self._diff()
            if self._changes is not None:
                if self._changes["properties"] is not None:
                    self.swis.update(self.uri, **self._changes["properties"])
                if self._changes["custom_properties"] is not None:
                    self.swis.update(
                        f"{self.uri}/CustomProperties",
                        **self._changes["custom_properties"],
                    )
                self.get(refresh=True)
                self._changes = None
                return True
            else:
                return False
        else:
            return self.create()
