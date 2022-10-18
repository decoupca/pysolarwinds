from logging import NullHandler, getLogger
from typing import Any, Dict, Union

from solarwinds.defaults import EXCLUDE_CUSTOM_PROPS
from solarwinds.exceptions import SWIDNotFound, SWObjectPropertyError
from solarwinds.utils import print_dict, sanitize_swdata

log = getLogger(__name__)
log.addHandler(NullHandler())


class Endpoint(object):
    endpoint = None
    uri = None
    id = None
    _exists = False
    _id_attr = None
    _swid_key = None
    _swquery_attrs = []
    _swargs_attrs = None
    _required_swargs_attrs = None
    _swargs = None
    _extra_swargs = None
    _swdata = None
    _changes = None
    _exclude_custom_props = EXCLUDE_CUSTOM_PROPS
    _child_objects = None

    def __init__(self):
        if self.exists():
            self.refresh()
        else:
            self._set_defaults()
        self._init_child_objects()
        self._update_attrs_from_children()

    def refresh(self) -> None:
        if self.exists():
            self._get_swdata()
            self._get_id()
            self._update_attrs(
                attr_updates=self._get_attr_updates(),
                cp_updates=self._get_cp_updates() or self._get_sw_cprops(),
            )
            self._update_child_attrs()
            self._refresh_child_objects()
            self._update_attrs_from_children()
        else:
            log.warning("object doesn't exist, can't refresh")

    def _set_defaults(self) -> None:
        """
        Set attribute defaults. Overridden in subclasses.
        """
        pass

    def _get_uri(self, refresh: bool = False) -> Union[str, None]:
        """
        Get object's SWIS URI
        """
        if self.uri is None or refresh is True:
            if not self._swquery_attrs:
                raise SWObjectPropertyError("Missing required property: _swquery_attrs")
            log.debug("uri is not set or refresh is True, updating...")
            queries = []
            for attr in self._swquery_attrs:
                v = getattr(self, attr)
                if v is not None:
                    k = attr.replace("_", "")
                    queries.append(
                        f"SELECT Uri as uri FROM {self.endpoint} WHERE {k} = '{v}'"
                    )
            if queries:
                query_lines = "\n".join(queries)
                log.debug(f"built SWQL queries:\n{query_lines}")
                for query in queries:
                    result = self._query(query)
                    if result:
                        uri = result["uri"]
                        log.debug(f"found uri: {uri}")
                        self.uri = uri
                        return uri
                return None
            else:
                key_attrs = ", ".join(self._swquery_attrs)
                log.debug(
                    f"Can't get uri, one of these key attributes must be set: {key_attrs}"
                )
                return None
        else:
            log.debug("self.uri is set and refresh is False, returning cached value")
            return self.uri

    def exists(self, refresh: bool = False) -> bool:
        """
        Whether or not object exists
        """
        self._exists = bool(self._get_uri(refresh=refresh))
        return self._exists

    def _get_swdata(self, refresh: bool = False, data: str = "both") -> None:
        """
        Caches solarwinds data
        """
        if not self._swdata or refresh is True:
            swdata = {"properties": None, "custom_properties": None}
            log.debug("getting object data from solarwinds...")
            if data == "both" or data == "properties":
                swdata["properties"] = sanitize_swdata(self.swis.read(self.uri))
            if data == "both" or data == "custom_properties":
                if hasattr(self, "custom_properties"):
                    swdata["custom_properties"] = sanitize_swdata(
                        self.swis.read(f"{self.uri}/CustomProperties")
                    )
            if (
                swdata.get("properties") is not None
                or swdata.get("custom_properties") is not None
            ):
                self._swdata = swdata
        else:
            log.debug("_swdata is already set and refresh is False, doing nothing")

    def _update_attrs(
        self,
        attr_updates: Union[Dict, None] = None,
        cp_updates: Union[Dict, None] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Updates object attributes from dict
        """
        if attr_updates is not None:
            for attr, new_v in attr_updates.items():
                v = getattr(self, attr)
                if v is None or overwrite is True:
                    setattr(self, attr, new_v)
                    log.debug(f"updated self.{attr} = {new_v}")
                else:
                    log.debug(
                        f"{attr} already has value '{v}' and overwrite is False, "
                        f"leaving intact"
                    )

        if cp_updates is not None:
            self.custom_properties = cp_updates or None

    def _get_cp_updates(self, overwrite: bool = False) -> dict:
        """
        Get updates to custom_properties
        """

        cprops = {}
        if self._swdata is not None:
            sw_cprops = self._swdata.get("custom_properties")
            if sw_cprops is not None:
                sw_cprops = {
                    k: v
                    for k, v in sw_cprops.items()
                    if k not in self._exclude_custom_props
                }
                if self.custom_properties is not None:
                    sw_cprops.update(self.custom_properties)
                    cprops = sw_cprops
        return cprops

    def _get_sw_cprops(self) -> dict:
        """
        Get customp properties from swdata
        """
        if self._swdata is not None:
            sw_cprops = self._swdata.get("custom_properties")
            if sw_cprops is not None:
                return {
                    k: v
                    for k, v in sw_cprops.items()
                    if k not in self._exclude_custom_props
                }

    def _get_attr_updates(self) -> dict:
        """
        Get attribute updates from self._swdata. Overridden in subclasses.
        """
        return {}

    def _init_child_objects(self) -> None:
        """
        Initialize child objects
        """
        if self._child_objects is not None:
            log.debug("initializing child objects...")
            for attr, props in self._child_objects.items():
                if not hasattr(self, attr):
                    setattr(self, attr, None)
                child_object = getattr(self, attr)

                if child_object is None:
                    child_class = props["class"]
                    child_args = {}

                    if props.get("init_args") is not None:
                        for parent_arg, child_arg in props["init_args"].items():
                            parent_value = getattr(self, parent_arg)
                            child_args[child_arg] = parent_value
                    # if all child args evaulate to none, don't initialize
                    all_child_args_unset = True
                    for v in child_args.values():
                        if v is not None:
                            all_child_args_unset = False
                    if all_child_args_unset is True:
                        log.debug(
                            f"all props for child object {attr} unset, not initializing child"
                        )
                    else:
                        log.debug(
                            f"initializing child object at self.{attr} with args {child_args}"
                        )
                        setattr(self, attr, child_class(self.swis, **child_args))
                else:
                    log.debug(
                        f"child object at self.{attr} already initialized, doing nothing"
                    )
        else:
            log.debug(f"no child objects found, doing nothing")

    def _update_child_attrs(self) -> None:
        """
        Update child attributes with self (parent) attributes, as mapped in self._child_objects
        """
        if self._child_objects is not None:
            for attr, props in self._child_objects.items():
                child = getattr(self, attr)
                if child is not None:
                    for local_attr, child_attr in props["attr_map"].items():
                        child_value = getattr(child, child_attr)
                        local_value = getattr(self, local_attr)
                        if local_value != child_value:
                            setattr(child, child_attr, local_value)
                            log.debug(
                                f'updated child attribute {child_attr} to "{local_value}" '
                                f"from local attribute {local_attr}"
                            )
                else:
                    log.debug(f"child object at {attr} is None, nothing to do")

    def _refresh_child_objects(self) -> None:
        """
        Call refresh() on all children
        """
        if self._child_objects is not None:
            for attr in self._child_objects.keys():
                child = getattr(self, attr)
                if child is not None:
                    child.refresh()

    def _create_child_objects(self) -> None:
        """
        Call create() on all children
        """
        if self._child_objects is not None:
            for attr in self._child_objects.keys():
                child = getattr(self, attr)
                child.create()

    def _update_attrs_from_children(self, overwrite: bool = False) -> None:
        """
        Update self (parent) attributes from child attributes, as mapped in self._child_objects
        """
        if self._child_objects is not None:
            for attr, props in self._child_objects.items():
                child = getattr(self, attr)
                if child is not None:
                    attr_updates = {}
                    for local_attr, child_attr in props["attr_map"].items():
                        child_value = getattr(child, child_attr)
                        local_value = getattr(self, local_attr)
                        if local_value != child_value or overwrite is True:
                            attr_updates.update({local_attr: child_value})
                            log.debug(
                                f"updated self.{local_attr} = {child_value} from child attr {child_attr}"
                            )
                    self._update_attrs(attr_updates=attr_updates)

    def _build_swargs(self) -> None:
        swargs = {"properties": None, "custom_properties": None}
        properties = {}
        custom_properties = {}
        for attr in self._swargs_attrs:
            value = getattr(self, attr)
            if value is not None:
                # store args without underscores so they match
                # solarwinds argument names
                attr = attr.replace("_", "")
                properties[attr] = value
                log.debug(f'_swargs["properties"]["{attr}"] = {value}')

        extra_swargs = self._get_extra_swargs()
        if extra_swargs:
            for k, v in extra_swargs.items():
                properties[k] = v
                log.debug(f'_swargs["properties"]["{k}"] = {v}')

        if hasattr(self, "custom_properties"):
            custom_properties = self.custom_properties
            log.debug(f'_swargs["custom_properties"] = {self.custom_properties}')

        swargs["properties"] = properties if properties else None
        swargs["custom_properties"] = custom_properties if custom_properties else None
        if (
            swargs.get("properties") is not None
            or swargs.get("custom_properties") is not None
        ):
            self._swargs = swargs

    def _get_swdata_value(self, key: str, data: str = "properties") -> Any:
        if self._swdata is not None:
            data = self._swdata.get(data)
            if data is not None:
                return data.get(key)

    def _get_extra_swargs(self) -> dict:
        # overwrite in subcasses if they have extra swargs
        return {}

    def _diff_properties(self) -> Union[dict, None]:
        changes = {}
        log.debug("diff'ing properties...")
        for k, sw_v in self._swdata["properties"].items():
            k = k.lower()
            local_v = self._swargs["properties"].get(k)
            if local_v:
                if local_v != sw_v:
                    changes[k] = local_v
                    log.debug(f"property {k} has changed from {sw_v} to {local_v}")
        if changes:
            return changes
        else:
            log.debug("no changes to properties found")
            return None

    def _diff_custom_properties(self) -> Union[dict, None]:
        changes = {}
        log.debug("diff'ing custom properties...")
        cp_args = self._swargs.get("custom_properties")
        cp_data = self._swdata.get("custom_properties")
        if cp_data is None and cp_args is not None:
            changes = cp_args
        if cp_args is not None and cp_data is not None:
            for k, v in cp_args.items():
                sw_v = cp_data.get(k)
                if sw_v != v:
                    changes[k] = v
                    log.debug(f'custom property {k} has changed from "{sw_v}" to "{v}"')
        if changes:
            return changes
        else:
            log.debug("no changes to custom_properties found")
            return None

    def _diff_child_objects(self) -> Union[dict, None]:
        changes = {}
        log.debug("diff'ing child objects...")
        if self._child_objects is not None:
            for attr in self._child_objects.keys():
                child = getattr(self, attr)
                if child is not None:
                    child._diff()
                    if child._changes is not None:
                        changes[attr] = child._changes
        if changes:
            return changes
        else:
            log.debug("no changes to child objects found")
            return None

    def _diff(self) -> None:
        self._build_swargs()
        self._update_child_attrs()
        changes = {}
        if self.exists():
            self._get_swdata()
            self._build_swargs()
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
            changes.get("properties") is not None
            or changes.get("custom_properties") is not None
            or changes.get("child_objects") is not None
        ):
            self._changes = changes
            log.debug(f"found changes: {changes}")
        else:
            log.debug("no changes found")

    def _get_id(self) -> None:
        if self._swdata is not None:
            sw_id = self._swdata["properties"].get(self._swid_key)
            if sw_id is not None:
                self.id = sw_id
                setattr(self, self._id_attr, sw_id)
                log.debug(f"got solarwinds object id {self.id}")
            else:
                raise SWIDNotFound(
                    f'Could not find id value in _swdata["{self._swid_key}"]'
                )
        else:
            log.debug("_swdata is None, can't get id")

    def create(self) -> bool:
        """Create object"""
        if self.exists():
            log.warning("object exists, can't create")
            return False
        else:
            self._build_swargs()
            if self._swargs is None:
                raise SWObjectPropertyError("Can't create object without properties.")
            for attr in self._required_swargs_attrs:
                if getattr(self, attr) is None:
                    raise SWObjectPropertyError(f"Missing required attribute: {attr}")

            self.uri = self.swis.create(self.endpoint, **self._swargs["properties"])
            log.debug("created object")
            if self._swargs.get("custom_properties") is not None:
                self.swis.update(
                    f"{self.uri}/CustomProperties",
                    **self._swargs["custom_properties"],
                )
                log.debug("added custom properties")
            self._init_child_objects()
            self._get_swdata()
            self._get_id()
            self._update_child_attrs()
            self._create_child_objects()
            self.refresh()
            return True

    def delete(self) -> bool:
        """Delete object"""
        if self.exists():
            self.swis.delete(self.uri)
            log.debug("deleted object")
            self.uri = None
            self._exists = False
            return True
        else:
            log.warning("object doesn't exist, doing nothing")
            return False

    def _query(self, query) -> dict:
        log.debug(f"executing SWIS query: {query}")
        return self.swis.query(query)

    def update(self) -> bool:
        """Update object in solarwinds with local object's properties"""
        self._build_swargs()
        if self.exists():
            if self._changes is None:
                log.debug("found no changes, running _diff()...")
                self._diff()
            if self._changes is not None:
                if self._changes.get("properties") is not None:
                    self.swis.update(self.uri, **self._changes["properties"])
                    log.info(
                        f"{self.name}: updated properties: {print_dict(self._changes['properties'])}"
                    )
                    self._get_swdata(refresh=True, data="properties")
                if self._changes.get("custom_properties") is not None:
                    self.swis.update(
                        f"{self.uri}/CustomProperties",
                        **self._changes["custom_properties"],
                    )
                    log.info(
                        f"{self.name}: updated custom properties: {print_dict(self._changes['custom_properties'])}"
                    )
                    self._get_swdata(refresh=True, data="custom_properties")
                if self._changes.get("child_objects") is not None:
                    log.debug("found changes to child objects")
                    for attr in self._changes["child_objects"].keys():
                        child = getattr(self, attr)
                        child.update()
                    log.info(f"{self.name}: updated child objects")
                self._changes = None
                return True
            else:
                log.info(f"{self.name}: found no changes, doing nothing")
                return False
        else:
            log.debug(f"{self.name}: object does not exist, creating...")
            return self.create()
