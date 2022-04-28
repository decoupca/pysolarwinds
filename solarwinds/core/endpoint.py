import inspect
import re

from solarwinds.core.exceptions import SWObjectPropertyError, SWUriNotFound
from solarwinds.core.logging import log
from solarwinds.utils import camel_to_snake, parse_response, sanitize_swdata


class Endpoint(object):
    name = None
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
    _exclude_custom_props = ["NodeID", "InstanceType", "Uri", "InstanceSiteId"]
    _attr_map = None
    _child_objects = None

    def _get_uri(self, refresh=False):
        """Get an object's SWIS URI"""
        if self.uri is None or refresh is True:
            log.debug("self.uri is not set or refresh is True, updating...")
            queries = []
            for key in self._keys:
                value = getattr(self, key)
                if value is not None:
                    sw_key = key.replace("_", "")
                    queries.append(
                        f"SELECT Uri as uri FROM {self.endpoint} WHERE {sw_key} = '{value}'"
                    )
            if queries:
                query_lines = "\n".join(queries)
                log.debug(f"built SWQL queries:\n{query_lines}")
                for query in queries:
                    result = self.query(query)
                    if result:
                        self.uri = result["uri"]
                        log.debug(f"found uri: {self.uri}")
                        return True
                raise SWUriNotFound(
                    f"No results found for any of these queries:\n{query_lines}"
                )
            else:
                key_props = ", ".join(self._keys)
                raise SWUriNotFound(
                    f"Must provide a value for at least one key property: {key_props}"
                )
        else:
            log.debug("self.uri is set or refresh is False, doing nothing")

    def _get_swdata(self, refresh=False, data="both"):
        """Caches solarwinds data about an object"""
        if self._swdata is None or refresh is True:
            log.debug("getting object data from solarwinds...")
            self._swdata = {}
            if data == "both" or data == "properties":
                self._swdata["properties"] = sanitize_swdata(self.swis.read(self.uri))
                log.debug('updated _swdata["properties"]')
                self._build_attr_map()
            if data == "both" or data == "custom_properties":
                if hasattr(self, "custom_properties"):
                    self._swdata["custom_properties"] = sanitize_swdata(
                        self.swis.read(f"{self.uri}/CustomProperties")
                    )
                    log.debug('updated _swdata["custom_properties"]')
        else:
            log.debug("self._swdata is set or refresh is False, doing nothing")

    def _init_child_objects(self):
        if self._child_objects is not None:
            log.debug("initializing child objects...")
            for child_object, props in self._child_objects.items():
                local_attr = props["local_attr"]
                child = getattr(self, local_attr)
                if child is None:
                    init_args = props["init_args"]
                    attr_map = props["attr_map"]
                    child_args = {}
                    for child_arg, parent_arg in init_args.items():
                        parent_v = getattr(self, parent_arg)
                        if parent_v is None:
                            raise SWObjectPropertyError(
                                f"Can't init child object {child_object}, "
                                f"parent arg {parent_arg} is None"
                            )
                        else:
                            child_args[child_arg] = parent_v
                    setattr(self, local_attr, child_object(self.swis, **child_args))
                    log.debug(f"initialized child object")
                    child = getattr(self, local_attr)
                    child.get()
                    for local_attr, child_attr in attr_map.items():
                        local_v = getattr(self, local_attr)
                        child_v = getattr(child, child_attr)
                        setattr(self, local_attr, child_v)
                        log.debug(
                            f'updated local attribute {local_attr} to "{child_v}" '
                            f"from child object attribute {child_attr}"
                        )
                else:
                    log.debug("child object already initialized, doing nothing")
        else:
            log.debug(f"no child objects found, doing nothing")

    def _build_attr_map(self):
        """builds a map of local attributes to solarwinds properties"""
        self._get_swdata()
        log.debug("building attribute map...")
        attr_map = {}
        for sw_k, sw_v in self._swdata["properties"].items():
            local_attr = camel_to_snake(sw_k)
            if hasattr(self, local_attr):
                attr_map[local_attr] = sw_k
                log.debug(f"added {local_attr} to attribute map")
            else:
                log.debug(f"{self.name} doesn't have attribute {local_attr}, skipping")
        if attr_map:
            self._attr_map = attr_map
        else:
            log.warning("found no attributes to map")

    def _update_object(self, overwrite=False):
        """changes local python object's properties with properties read from solarwinds
        if overwrite=False, will not update any attributes that are already set
        """
        self._serialize()
        log.debug(f"updating object attributes from solarwinds data...")
        for local_attr, sw_attr in self._attr_map.items():
            local_v = getattr(self, local_attr)
            if local_v is None or overwrite is True:
                sw_v = self._swdata["properties"][sw_attr]
                setattr(self, local_attr, sw_v)
                log.debug(f"updated attribute: {local_attr} = {sw_v}")
            else:
                log.debug(
                    "attribute already has a value and overwrite is False, "
                    "leaving value intact"
                )
        if self._swdata.get("custom_properties") is not None:
            log.debug("updating custom properties...")
            cprops = {}
            for k, v in self._swdata["custom_properties"].items():
                if k not in self._exclude_custom_props or overwrite is True:
                    log.debug(f"updating custom property {k} = {v}")
                    cprops[k] = v
            if cprops:
                self.custom_properties = cprops
        else:
            log.debug(
                f"{self.name} does not have custom_properties attribute, "
                "not updating custom properties"
            )

    def _serialize(self):
        log.debug("serializing object attributes to _localdata...")
        self._build_attr_map()
        serialized = {"properties": {}, "custom_properties": None}
        args = inspect.getfullargspec(self.__init__)[0]
        exclude_attrs = ["self", "swis", "custom_properties"]
        exclude_attrs.extend(self._exclude_attrs)
        log.debug(f"excluding attributes from serialization: {exclude_attrs}")
        for arg in args:
            if arg not in exclude_attrs:
                value = getattr(self, arg)
                # store args without underscores so they match
                # solarwinds argument names
                arg = arg.replace("_", "")
                if self._localdata["properties"][arg] != value:
                    serialized["properties"][arg] = value
                    log.debug(f'updated _localdata["properties"][{arg}] = {value}')
                else:
                    log.debug("attribute {arg} has not changed, doing nothing")
        if hasattr(self, "custom_properties"):
            if self.custom_properties is not None:
                if serialized["custom_properties"] != self.custom_properties:
                    serialized["custom_properties"] = self.custom_properties
                    log.debug(
                        'copied custom_properties attribute to _localdata["custom_properties"]'
                    )
                else:
                    log.debug(
                        "custom_properties attribute already matches _localdata, doing nothing"
                    )
        self._localdata = serialized
        if self._child_objects is not None:
            log.debug("serializing child objects...")
            for child_object, props in self._child_objects.items():
                attr_map = props["attr_map"]
                local_attr = props["local_attr"]
                child = getattr(self, local_attr)
                for local_attr, child_attr in attr_map.items():
                    local_v = getattr(self, local_attr)
                    child_v = getattr(child, child_attr)
                    if local_v != child_v:
                        setattr(child, child_attr, local_v)
                        log.debug(
                            f"updated child object attribute {child_attr} = {local_v}"
                        )
                    else:
                        log.debug(
                            "child attribute {child_attr} value already matches "
                            "local attribute value, doing nothing"
                        )
                child._serialize()

    def _diff_properties(self):
        changes = {}
        if self._swdata is None:
            self._get_swdata()
        for k, sw_v in self._swdata["properties"].items():
            k = k.lower()
            if self._localdata["properties"] is not None:
                local_v = self._localdata["properties"].get(k)
                if local_v:
                    if local_v != sw_v:
                        changes[k] = local_v
                        log.debug("property {k} has changed from {sw_v} to {local_v}")
        if changes:
            return changes
        else:
            log.debug("no changes to properties found")

    def _diff_custom_properties(self):
        changes = {}
        if self._swdata is None:
            self._get_swdata()
        for k, local_v in self._localdata["custom_properties"].items():
            if k not in self._swdata["custom_properties"].keys():
                changes[k] = local_v
            sw_v = self._swdata["custom_properties"].get(k)
            if sw_v != local_v:
                changes[k] = local_v
                log.debug("custom property {k} has changed from {sw_v} to {local_v}")
        if changes:
            return changes
        else:
            log.debug("no changes to custom_properties found")

    def _diff_child_objects(self):
        changes = {}
        if self._child_objects is not None:
            for child_object, props in self._child_objects.items():
                child = getattr(self, props["local_attr"])
                child._diff()
                if child._changes is not None:
                    changes[child_object] = child._changes
        if changes:
            return changes

    def _diff(self):
        self._serialize()
        changes = {}
        if self.exists():
            changes["properties"] = self._diff_properties()
            if hasattr(self, "custom_properties"):
                changes["custom_properties"] = self._diff_custom_properties()
            if self._child_objects is not None:
                changes["child_objects"] = self._diff_child_objects()
        else:
            changes["properties"] = self._localdata.get("properties")
            if hasattr(self, "custom_properties"):
                changes["custom_properties"] = self._localdata.get("custom_properties")
            if self._child_objects is not None:
                changes["child_objects"] = self._diff_child_objects()
        if (
            changes.get("properties") is not None
            or changes.get("custom_properties") is not None
            or changes.get("child_objects") is not None
        ):
            self._changes = changes
        else:
            log.debug(f"found no changes")

    def _get_id(self):
        self.id = int(re.search(r"(\d+)$", self.uri).group(0))
        log.debug(f"get_id(): got id: {self.id}")

    def create(self):
        """Create object"""
        if self.exists():
            log.warning("object exists, can't create")
            return False
        else:
            self._serialize()
            if self._localdata is None:
                raise SWObjectPropertyError("Can't create object without properties.")
            else:
                self.uri = self.swis.create(
                    self.endpoint, **self._localdata["properties"]
                )
                log.debug("created object")
                if self._child_objects is not None:
                    log.debug("creating child objects...")
                    for child_object, props in self._child_objects.items():
                        getattr(self, props["local_attr"]).create()
                return True

    def delete(self):
        """Delete object"""
        if self.exists():
            self.swis.delete(self.uri)
            log.debug("deleted object")
            self.uri = None
            return True
        else:
            log.warning("object doesn't exist")
            return False

    def exists(self, refresh=False):
        """Whether or not an object exists"""
        if self.uri is not None:
            log.debug("self.uri is set, object exists")
            return True
        if self.uri is None or refresh is True:
            try:
                self._get_uri()
                log.debug("found uri from solarwinds, object exists")
                return True
            except SWUriNotFound:
                log.debug("solarwinds uri not found, object does not exist")
                return False

    def get(self, refresh=False, overwrite=False):
        """Gets object data from solarwinds and updates local object attributes"""
        if self.exists(refresh=refresh):
            log.debug("getting object details...")
            self._get_swdata(refresh=refresh)
            self._update_object(overwrite=overwrite)
            self._init_child_objects()
        else:
            log.warning("object doesn't exist, nothing to get")

    def query(self, query):
        log.debug(f"executing SWIS query: {query}")
        return parse_response(self.swis.query(query))

    def update(self):
        """Update object in solarwinds with local object's properties"""
        self._serialize()
        if self.exists():
            if self._changes is None:
                log.debug("found no changes, running _diff()...")
                self._diff()
            if self._changes is not None:
                log.debug("found changes")
                if self._changes.get("properties") is not None:
                    log.debug("found changes to properties")
                    self.swis.update(self.uri, **self._changes["properties"])
                    log.info(f"updated properties")
                    self._get_swdata(refresh=True, data="properties")
                if self._changes.get("custom_properties") is not None:
                    log.debug("found changes to custom properties")
                    self.swis.update(
                        f"{self.uri}/CustomProperties",
                        **self._changes["custom_properties"],
                    )
                    log.info(f"updated custom properties")
                    self._get_swdata(refresh=True, data="custom_properties")
                if self._changes.get("child_objects") is not None:
                    log.debug("found changes to child objects")
                    for child_object, changes in self._changes["child_objects"].items():
                        props = self._child_objects[child_object]
                        child = getattr(self, props["local_attr"])
                        child.update()
                    log.info(f"updated child objects")
                self._changes = None
                return True
            else:
                log.warning("found no changes to update, doing nothing")
                return False
        else:
            log.debug("object does not exist, creating...")
            return self.create()
