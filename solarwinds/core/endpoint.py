import inspect
import re

from solarwinds.core.exceptions import SWObjectPropertyError, SWUriNotFound, SWIDNotFound
from solarwinds.utils import camel_to_snake, parse_response, sanitize_swdata
from logging import getLogger, NullHandler
from pprint import pprint


class Endpoint(object):
    # solarwinds endpoint (e.g. Orion.Nodes)
    endpoint = None

    # solarwinds object uri
    uri = None

    # object-agnostic solarwinds id
    id = None

    # object-specific id attribute to store id in (e.g. node_id)
    # shoul also correspond to swdata key (nodeid)
    _id_attr = None

    # key in solarwinds data to read ID value from
    _sw_id_key = None

    # local attrs to use as keys when building solarwinds queries
    _swquery_attrs = None

    # local attrs to use when building solarwinds arguments
    # (not all local attrs correspond directly to solarwinds args)
    _swargs_attrs = None

    # solarwinds arguments when built live here
    _swargs = None

    # place to hold any other swargs that might not directly map to 
    # object attributes
    _extra_swargs = None

    # cached solarwinds data lives here
    _swdata = None

    # diff between swdata and swargs
    _changes = None

    # keys to exclude when building custom properties for swargs
    _exclude_custom_props = ["DisplayName", "NodeID", "InstanceType", "Uri", "InstanceSiteId"]

    # dynamically generated map of local object attrs to solarwinds args
    _attr_map = None

    # map of child (dependent) objects
    _child_objects = None

    def __init__(self):
        self.log = getLogger(__name__)
        self.log.addHandler(NullHandler())
        self._init_child_objects()
        self._build_swargs()
        self._update_child_objects()

    def _get_uri(self, refresh=False):
        """Get an object's SWIS URI"""
        if self.uri is None or refresh is True:
            self.log.debug("self.uri is not set or refresh is True, updating...")
            queries = []
            for key in self._swquery_attrs:
                value = getattr(self, key)
                if value is not None:
                    sw_key = key.replace("_", "")
                    queries.append(
                        f"SELECT Uri as uri FROM {self.endpoint} WHERE {sw_key} = '{value}'"
                    )
            if queries:
                query_lines = "\n".join(queries)
                self.log.debug(f"built SWQL queries:\n{query_lines}")
                for query in queries:
                    result = self.query(query)
                    if result:
                        self.uri = result["uri"]
                        self.log.debug(f"found uri: {self.uri}")
                        return True
                raise SWUriNotFound(
                    f"No results found for any of these queries:\n{query_lines}"
                )
            else:
                key_props = ", ".join(self._swquery_attrs)
                raise SWUriNotFound(
                    f"Must provide a value for at least one key property: {key_props}"
                )
        else:
            self.log.debug("self.uri is set or refresh is False, doing nothing")

    def _get_swdata(self, refresh=False, data="both"):
        """Caches solarwinds data about an object"""
        if self._swdata is None or refresh is True:
            self.log.debug("getting object data from solarwinds...")
            swdata = {}
            if data == "both" or data == "properties":
                swdata["properties"] = sanitize_swdata(self.swis.read(self.uri))
            if data == "both" or data == "custom_properties":
                if hasattr(self, "custom_properties"):
                    swdata["custom_properties"] = sanitize_swdata(
                        self.swis.read(f"{self.uri}/CustomProperties")
                    )
            if swdata:
                self._swdata = swdata
                self._build_attr_map()
                self._get_id()
        else:
            self.log.debug(
                "self._swdata is already set and refresh is False, doing nothing"
            )

    def _init_child_objects(self):
        if self._child_objects is not None:
            self.log.debug("initializing child objects...")
            for child_class, child_props in self._child_objects.items():

                # initialize child object attribute
                child_attr = child_props['child_attr']
                if not hasattr(self, child_attr):
                    setattr(self, child_attr, None)
                child_object = getattr(self, child_attr)

                if child_object is None:
                    child_args = {}

                    # some child classes might need args to init.
                    # most should be able to init without any args, but just in case,
                    # here we provide the option.
                    if child_props.get("init_args") is not None:
                        for child_arg, parent_arg in child_props["init_args"].items():
                            parent_value = getattr(self, parent_arg)
                            if parent_value is None:
                                raise SWObjectPropertyError(
                                    f"Can't init child object {child_class}, "
                                    f"parent arg {parent_arg} is None"
                                )
                            else:
                                child_args[child_arg] = parent_value

                    # initialize child object
                    setattr(self, child_attr, child_class(self.swis, **child_args))
                    self.log.debug(f"initialized child object at {child_attr}")
                else:
                    self.log.debug("child object already initialized, doing nothing")
        else:
            self.log.debug(f"no child objects found, doing nothing")

    def _update_child_objects(self):
        """updates child attrs from parent attrs defined in _child_attrs
        and builds child swargs
        """
        if self._child_objects is not None:
            for child_class, child_props in self._child_objects.items():
                child_object = getattr(self, child_props["child_attr"])
                if child_object is not None:
                    for local_attr, child_attr in child_props["attr_map"].items():
                        local_value = getattr(self, local_attr)
                        setattr(child_object, child_attr, local_value)
                        self.log.debug(
                            f'updated child attribute {child_props["child_attr"]} to "{local_value}" '
                            f"from local attribute {local_attr}"
                        )
                    child_object._build_swargs()
                else:
                    self.log.warning(
                        f'child object at {child_props["child_attr"]} is None, cannot update'
                    )
        else:
            self.log.warning("self._child_objects is None, nothing to update")

    def _build_attr_map(self):
        """builds a map of local attributes to solarwinds properties"""
        if self._attr_map is None:
            self.log.debug("building attribute map...")
            attr_map = {}
            for sw_k, sw_v in self._swdata["properties"].items():
                local_attr = camel_to_snake(sw_k)
                if hasattr(self, local_attr):
                    attr_map[local_attr] = sw_k
                    self.log.debug(f"added {local_attr} to attribute map")
            if attr_map:
                self._attr_map = attr_map
            else:
                self.log.warning("found no attributes to map")
        else:
            self.log.debug("attributes already mapped, doing nothing")

    def _update_object(self, overwrite=False):
        """changes local python object's properties with properties read from solarwinds
        if overwrite=False, will not update any attributes that are already set
        """
        if self._swdata is not None:
            self.log.debug(f"updating object attributes from solarwinds data...")
            for local_attr, sw_attr in self._attr_map.items():
                local_value = getattr(self, local_attr)
                if local_value is None or overwrite is True:
                    sw_value = self._swdata["properties"][sw_attr]
                    setattr(self, local_attr, sw_value)
                    self.log.debug(f"updated attribute: {local_attr} = {sw_value}")
                else:
                    self.log.debug(
                        f"attribute {local_attr} already has value and overwrite is False, "
                        f"leaving local value {local_value} intact"
                    )
            # custom properties
            if self._swdata.get("custom_properties") is not None:
                if hasattr(self, "custom_properties"):
                    if self.custom_properties is not None:
                        self.log.debug("updating custom properties...")
                        cprops = {}
                        for k, v in self._swdata["custom_properties"].items():
                            if k not in self._exclude_custom_props:
                                local_value = self.custom_properties.get(k)
                                if local_value is None or overwrite is True:
                                    cprops[k] = v
                                    self.log.debug(f"custom property {k} = {v}")

                        if cprops:
                            self.custom_properties.update(cprops)
                            self.log.debug(
                                f"updated self.custom_properties with {cprops}"
                            )
                        else:
                            self.log.debug(
                                f"no custom properties to update, doing nothing"
                            )
                else:
                    self.log.debug(
                        f"{self.name} object does not have custom_properties attribute, "
                        "not updating custom properties"
                    )
        else:
            self.log.warning("self._swdata is None, can't update object")

    def _build_swargs(self):
        swargs = {"properties": {}, "custom_properties": {}}
        self.log.debug("building swargs...")

        # properties
        args = inspect.getfullargspec(self.__init__)[0]
        for arg in args:
            if arg in self._swargs_attrs:
                value = getattr(self, arg)
                # store args without underscores so they match
                # solarwinds argument names
                arg = arg.replace("_", "")
                swargs["properties"][arg] = value
                self.log.debug(f'_swargs["properties"]["{arg}"] = {value}')

        # extra swargs
        extra_swargs = self._get_extra_swargs()
        if extra_swargs:
            for k, v in extra_swargs.items():
                swargs['properties'][k] = v
                self.log.debug(f'_swargs["properties"]["{k}"] = {v}')

        # custom properties
        if hasattr(self, "custom_properties"):
            swargs["custom_properties"] = self.custom_properties
            self.log.debug(f'_swargs["custom_properties"] = {self.custom_properties}')

        # update _swargs
        if swargs["properties"] or swargs["custom_properties"]:
            self._swargs = swargs

        # child objects
        self._update_child_objects()

    def _get_extra_swargs(self):
        # overwrite in subcasses if they have extra swargs
        return {}

    def _diff_properties(self):
        changes = {}
        self.log.debug("diff'ing properties...")
        for k, sw_v in self._swdata["properties"].items():
            k = k.lower()
            local_v = self._swargs["properties"].get(k)
            if local_v:
                if local_v != sw_v:
                    changes[k] = local_v
                    self.log.debug(f"property {k} has changed from {sw_v} to {local_v}")
        if changes:
            return changes
        else:
            self.log.debug("no changes to properties found")

    def _diff_custom_properties(self):
        changes = {}
        self.log.debug("diff'ing custom properties...")
        if self._swargs['custom_properties'] is not None:
            for k, local_v in self._swargs["custom_properties"].items():
                if k not in self._swdata["custom_properties"].keys():
                    changes[k] = local_v
                sw_v = self._swdata["custom_properties"].get(k)
                if sw_v != local_v:
                    changes[k] = local_v
                    self.log.debug(
                        f'custom property {k} has changed from "{sw_v}" to "{local_v}"'
                    )
        if changes:
            return changes
        else:
            self.log.debug("no changes to custom_properties found")

    def _diff_child_objects(self):
        changes = {}
        self.log.debug("diff'ing child objects...")
        if self._child_objects is not None:
            for child_class, child_props in self._child_objects.items():
                child_object = getattr(self, child_props["child_attr"])
                child_object._diff()
                if child_object._changes is not None:
                    changes[child_object] = child_object._changes
        if changes:
            return changes

    def _diff(self):
        changes = {}
        self._build_swargs()
        if self.exists():
            self._get_swdata()
            changes = {
                "properties": self._diff_properties(),
                "custom_properties": self._diff_custom_properties(),
                "child_objects": self._diff_child_objects(),
            }
        else:
            changes = {
                "properties": self._swargs["properties"],
                "custom_properties": self._swargs["custom_properties"],
                "child_objects": self._diff_child_objects(),
            }
        if (
            changes["properties"] is not None
            or changes["custom_properties"] is not None
            or changes["child_objects"] is not None
        ):
            self._changes = changes
            self.log.debug(f"found changes: {changes}")
        else:
            self.log.debug("no changes found")

    def _get_id(self):
        if self._swdata is not None:
            object_id = self._swdata['properties'].get(self._sw_id_key)
            if object_id is not None:
                self.id = object_id
                setattr(self, self._id_attr, object_id)
                self.log.debug(f"got solarwinds object id {self.id}")
            else:
                raise SWIDNotFound(f'Could not find id value in _swdata["{self._sw_id_key}"]')
        else:
            self.log.debug("_swdata is None, can't get id")

    def create(self):
        """Create object"""
        if self.exists():
            self.log.warning("object exists, can't create")
            return False
        else:
            self._build_swargs()
            if self._swargs is None:
                raise SWObjectPropertyError("Can't create object without properties.")
            else:
                self.uri = self.swis.create(
                    self.endpoint, **self._swargs["properties"]
                )
                self.log.debug("created object")
                if self._swargs['custom_properties']:
                    self.swis.update(f'{self.uri}/CustomProperties', **self._swargs['custom_properties'])
                    self.log.debug("added custom properties")
                self._get_id()
                self._get_swdata()
                self._update_object()
                if self._child_objects is not None:
                    # child objects usually (always?) rely on IDs from parent objects
                    # that we don't have until we create the parent object
                    self._update_child_objects()
                    for child_class, child_props in self._child_objects.items():
                        child_object = getattr(self, child_props['child_attr'])
                        # though unlikely, a child object may exist when a parent
                        # object doesn't
                        if child_object.exists():
                            child_object.update()
                        else:
                            child_object.create()
                return True

    def delete(self):
        """Delete object"""
        if self.exists():
            self.swis.delete(self.uri)
            self.log.debug("deleted object")
            self.uri = None
            return True
        else:
            self.log.warning("object doesn't exist")
            return False

    def exists(self, refresh=False):
        """Whether or not an object exists"""
        if self.uri is None or refresh is True:
            try:
                self._get_uri()
                self.log.debug("found uri from solarwinds, object exists")
                return True
            except SWUriNotFound:
                self.log.debug("solarwinds uri not found, object does not exist")
                return False
        else:
            self.log.debug("self.uri is set, object exists")
            return True
            

    def get(self, refresh=False, overwrite=False):
        """Gets object data from solarwinds and updates local object attributes"""
        if self.exists(refresh=refresh):
            self.log.debug("getting object details...")
            self._get_swdata(refresh=refresh)
            self._update_object(overwrite=overwrite)
            self._build_swargs()
        else:
            self.log.warning("object doesn't exist, nothing to get")

    def query(self, query):
        self.log.debug(f"executing SWIS query: {query}")
        return parse_response(self.swis.query(query))

    def update(self):
        """Update object in solarwinds with local object's properties"""
        self._build_swargs()
        if self.exists():
            if self._changes is None:
                self.log.debug("found no changes, running _diff()...")
                self._diff()
            if self._changes is not None:
                if self._changes.get("properties") is not None:
                    self.swis.update(self.uri, **self._changes["properties"])
                    self.log.info(f"updated properties")
                    self._get_swdata(refresh=True, data="properties")
                if self._changes.get("custom_properties") is not None:
                    self.swis.update(
                        f"{self.uri}/CustomProperties",
                        **self._changes["custom_properties"],
                    )
                    self.log.info(f"updated custom properties")
                    self._get_swdata(refresh=True, data="custom_properties")
                if self._changes.get("child_objects") is not None:
                    self.log.debug("found changes to child objects")
                    for child_object, changes in self._changes["child_objects"].items():
                        child_props = self._child_objects[child_object.__class__]
                        child_object = getattr(self, child_props["child_attr"])
                        child_object.update()
                    self.log.info(f"updated child objects")
                self._changes = None
                return True
            else:
                self.log.warning("found no changes to update, doing nothing")
                return False
        else:
            self.log.debug("object does not exist, creating...")
            return self.create()
