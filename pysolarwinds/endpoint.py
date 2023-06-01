import datetime
from typing import Dict, Optional

from pysolarwinds.defaults import EXCLUDE_CUSTOM_PROPS
from pysolarwinds.exceptions import (
    SWIDNotFound,
    SWObjectDoesNotExist,
    SWObjectExists,
    SWObjectPropertyError,
)
from pysolarwinds.logging import get_logger
from pysolarwinds.swis import SWISClient
from pysolarwinds.utils import print_dict, sanitize_swdata

logger = get_logger(__name__)


class Endpoint:
    endpoint = None
    _attr_map = None
    _endpoint_attrs = None
    _type = None
    _id_attr = None
    _swid_key = None
    _swquery_attrs = None
    _swargs_attrs = None
    _required_swargs_attrs = None
    _child_objects = None

    def __init__(self):
        self.uri = None
        self._exists = False
        self._extra_swargs = None
        self._changes = None
        self._exclude_custom_props = EXCLUDE_CUSTOM_PROPS
        self._child_objects = None
        self._schema_version = "2020.2"
        self._swdata = {"properties": {}, "custom_properties": {}}
        if self.exists():
            self.refresh()
        else:
            self._set_defaults()
        self._call_init_methods()
        self._resolve_endpoint_attrs()
        self._update_attrs_from_children()

    def _call_init_methods(self):
        init_methods = [getattr(self, x) for x in dir(self) if x.startswith("_init")]
        for method in init_methods:
            method()

    def _resolve_endpoint_attrs(self) -> None:
        if self._endpoint_attrs:
            for attr, endpoint_class in self._endpoint_attrs.items():
                value = getattr(self, attr)
                if value:
                    if not isinstance(value, endpoint_class):
                        if isinstance(value, int):
                            endpoint = endpoint_class(swis=self.swis, id=value)
                        elif isinstance(value, str):
                            endpoint = endpoint_class(swis=self.swis, name=value)
                        setattr(self, attr, endpoint)
                    else:
                        endpoint = value
                        if not endpoint.exists():
                            raise SWObjectPropertyError(f"{endpoint} does not exist")

    @property
    def _schema_doc_url(self) -> str:
        base_url = f"http://solarwinds.github.io/OrionSDK/{self._schema_version}/schema"
        if self.endpoint:
            return f"{base_url}/{self.endpoint}.html"
        else:
            return base_url

    @property
    def _swp(self):
        """convenience alias"""
        return self._swdata["properties"]

    @property
    def _swcp(self):
        """convenience alias"""
        return self._swdata["custom_properties"]

    @property
    def instance_type(self) -> Optional[str]:
        return self._swp.get("InstanceType")

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
            logger.warning("object doesn't exist, nothing to refresh")

    def _set_defaults(self) -> None:
        """
        Set attribute defaults. Overridden in subclasses.
        """
        pass

    def _get_uri(self, refresh: bool = False) -> Optional[str]:
        """
        Get object's SWIS URI
        """
        if not self.uri or refresh:
            if not self._swquery_attrs:
                raise SWObjectPropertyError("Missing required property: _swquery_attrs")
            logger.debug("uri is not set or refresh is True, updating...")
            queries = []
            for attr in self._swquery_attrs:
                v = getattr(self, attr)
                if v:
                    k = self._attr_map[attr]
                    queries.append(
                        f"SELECT Uri as uri FROM {self.endpoint} WHERE {k} = '{v}'"
                    )
            if queries:
                query_lines = "\n".join(queries)
                logger.debug(f"built SWQL queries:\n{query_lines}")
                for query in queries:
                    result = self.swis.query(query)
                    if result:
                        uri = result[0]["uri"]
                        logger.debug(f"found uri: {uri}")
                        self.uri = uri
                        return uri
                return None
            else:
                key_attrs = ", ".join(self._swquery_attrs)
                logger.debug(
                    f"Can't get uri, one of these key attributes must be set: {key_attrs}"
                )
                return None
        else:
            logger.debug("self.uri is set and refresh is False, returning cached value")
            return self.uri

    def exists(self, refresh: bool = False) -> bool:
        """
        Whether or not object exists
        """
        self._exists = bool(self._get_uri(refresh=refresh))
        return self._exists

    def _get_swdata(self, refresh: bool = False, data: str = "both") -> None:
        """
        Caches pysolarwinds data
        """
        if not self.exists():
            raise SWObjectDoesNotExist()
        else:
            if (
                not self._swdata.get("properties")
                and not self._swdata.get("custom_properties")
            ) or refresh:
                swdata = {"properties": None, "custom_properties": None}
                logger.debug("getting object data from pysolarwinds...")
                if data == "both" or data == "properties":
                    swdata["properties"] = sanitize_swdata(self.swis.read(self.uri))
                if data == "both" or data == "custom_properties":
                    if hasattr(self, "custom_properties"):
                        swdata["custom_properties"] = sanitize_swdata(
                            self.swis.read(f"{self.uri}/CustomProperties")
                        )
                if swdata.get("properties") or swdata.get("custom_properties"):
                    self._swdata = swdata
            else:
                logger.debug(
                    "_swdata is already set and refresh is False, doing nothing"
                )

    def _update_attrs(
        self,
        attr_updates: Optional[Dict] = None,
        cp_updates: Optional[Dict] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Updates object attributes from dict
        """
        if attr_updates is None:
            attr_updates = self._get_attr_updates()

        for attr, new_v in attr_updates.items():
            v = getattr(self, attr)
            if not v or overwrite:
                setattr(self, attr, new_v or None)
                logger.debug(f"updated self.{attr} = {new_v}")
            else:
                logger.debug(
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
        if self._swdata:
            sw_cprops = self._swdata.get("custom_properties")
            if sw_cprops:
                sw_cprops = {
                    k: v
                    for k, v in sw_cprops.items()
                    if k not in self._exclude_custom_props
                }
                if self.custom_properties:
                    sw_cprops.update(self.custom_properties)
                    cprops = sw_cprops
        return cprops

    def _get_sw_cprops(self) -> dict:
        """
        Get customp properties from swdata
        """
        if self._swdata:
            sw_cprops = self._swdata.get("custom_properties")
            if sw_cprops:
                return {
                    k: v
                    for k, v in sw_cprops.items()
                    if k not in self._exclude_custom_props
                }
        return {}

    def _get_attr_updates(self) -> Dict:
        """
        Get attribute updates from self._swdata. Overridden in subclasses.
        """
        pass

    def _init_child_objects(self) -> None:
        """
        Initialize child objects
        """
        if self._child_objects:
            logger.debug("initializing child objects...")
            for attr, props in self._child_objects.items():
                if not hasattr(self, attr):
                    setattr(self, attr, None)
                child_object = getattr(self, attr)

                if not child_object:
                    child_class = props["class"]
                    child_args = {}

                    if props.get("init_args"):
                        for parent_arg, child_arg in props["init_args"].items():
                            parent_value = getattr(self, parent_arg)
                            child_args[child_arg] = parent_value
                    # if all child args evaulate to none, don't initialize
                    all_child_args_unset = True
                    for v in child_args.values():
                        if v:
                            all_child_args_unset = False
                    if all_child_args_unset:
                        logger.debug(
                            f"all props for child object {attr} unset, not initializing child"
                        )
                    else:
                        logger.debug(
                            f"initializing child object at self.{attr} with args {child_args}"
                        )
                        setattr(self, attr, child_class(self.swis, **child_args))
                else:
                    logger.debug(
                        f"child object at self.{attr} already initialized, doing nothing"
                    )
        else:
            logger.debug(f"no child objects found, doing nothing")

    def _update_child_attrs(self) -> None:
        """
        Update child attributes with self (parent) attributes, as mapped in self._child_objects
        """
        if self._child_objects:
            for attr, props in self._child_objects.items():
                child = getattr(self, attr)
                if child:
                    for local_attr, child_attr in props["attr_map"].items():
                        child_value = getattr(child, child_attr)
                        local_value = getattr(self, local_attr)
                        if local_value != child_value:
                            setattr(child, child_attr, local_value)
                            logger.debug(
                                f'updated child attribute {child_attr} to "{local_value}" '
                                f"from local attribute {local_attr}"
                            )
                else:
                    logger.debug(f"child object at {attr} is None, nothing to do")

    def _refresh_child_objects(self) -> None:
        """
        Call refresh() on all children
        """
        if self._child_objects:
            for attr in self._child_objects.keys():
                child = getattr(self, attr)
                if child:
                    child.refresh()

    def _create_child_objects(self) -> None:
        """
        Call create() on all children
        """
        if self._child_objects:
            for attr in self._child_objects.keys():
                child = getattr(self, attr)
                child.create()

    def _update_attrs_from_children(self, overwrite: bool = False) -> None:
        """
        Update self (parent) attributes from child attributes, as mapped in self._child_objects
        """
        if self._child_objects:
            for attr, props in self._child_objects.items():
                child = getattr(self, attr)
                if child:
                    attr_updates = {}
                    for local_attr, child_attr in props["attr_map"].items():
                        child_value = getattr(child, child_attr)
                        local_value = getattr(self, local_attr)
                        if local_value != child_value or overwrite is True:
                            attr_updates.update({local_attr: child_value})
                            logger.debug(
                                f"updated self.{local_attr} = {child_value} from child attr {child_attr}"
                            )
                    self._update_attrs(attr_updates=attr_updates)

    def _build_swargs(self) -> None:
        swargs = {"properties": None, "custom_properties": None}
        properties = {}
        custom_properties = {}
        for attr in self._swargs_attrs:
            value = getattr(self, attr)
            swarg = self._attr_map[attr]
            properties[swarg] = value
            logger.debug(f'_swargs["properties"]["{swarg}"] = {value}')

        extra_swargs = self._get_extra_swargs()
        if extra_swargs:
            for k, v in extra_swargs.items():
                properties[k] = v
                logger.debug(f'_swargs["properties"]["{k}"] = {v}')

        if hasattr(self, "custom_properties"):
            custom_properties = self.custom_properties
            logger.debug(f'_swargs["custom_properties"] = {self.custom_properties}')

        swargs["properties"] = properties
        swargs["custom_properties"] = custom_properties
        if swargs.get("properties") or swargs.get("custom_properties"):
            self._swargs = swargs

    def _get_extra_swargs(self) -> dict:
        # overwrite in subcasses if they have extra swargs
        return {}

    def _diff_properties(self) -> Optional[Dict]:
        changes = {}
        logger.debug("diff'ing properties...")
        # we need to convert empty values to NoneType for comparison, but
        # back to empty strings for SW API compatibility
        for k, local_v in self._swargs["properties"].items():
            local_v = local_v or None
            sw_v = self._swdata["properties"].get(k) or None
            if local_v != sw_v:
                changes[k] = local_v or ""
                logger.debug(f"property {k} has changed from {sw_v} to {local_v}")
        if changes:
            return changes
        else:
            logger.debug("no changes to properties found")
            return None

    def _diff_custom_properties(self) -> Optional[Dict]:
        changes = {}
        logger.debug("diff'ing custom properties...")
        cp_args = self._swargs.get("custom_properties")
        cp_data = self._swdata.get("custom_properties")
        if cp_data and not cp_args:
            changes = cp_args
        if cp_args and cp_data:
            for k, v in cp_args.items():
                sw_v = cp_data.get(k)
                if sw_v != v:
                    changes[k] = v
                    logger.debug(
                        f'custom property {k} has changed from "{sw_v}" to "{v}"'
                    )
        if changes:
            return changes
        else:
            logger.debug("no changes to custom_properties found")
            return None

    def _diff_child_objects(self) -> Optional[Dict]:
        changes = {}
        logger.debug("diff'ing child objects...")
        if self._child_objects:
            for attr in self._child_objects.keys():
                child = getattr(self, attr)
                if child:
                    child._diff()
                    if child._changes:
                        changes[attr] = child._changes
        if changes:
            return changes
        else:
            logger.debug("no changes to child objects found")
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
            changes.get("properties")
            or changes.get("custom_properties")
            or changes.get("child_objects")
        ):
            self._changes = changes
            logger.debug(f"found changes: {changes}")
        else:
            logger.debug("no changes found")

    def _get_id(self) -> None:
        if not self._swdata:
            self._get_swdata()
        sw_id = self._swdata["properties"].get(self._swid_key)
        if sw_id:
            self.id = sw_id
            setattr(self, self._id_attr, sw_id)
            logger.debug(f"got pysolarwinds object id {self.id}")
        else:
            raise SWIDNotFound(
                f'could not find id value in _swdata["properties"]["{self._swid_key}"]'
            )

    def create(self) -> bool:
        """Create object"""
        if self.exists():
            raise SWObjectExists("object exists, cannot create")
        else:
            self._resolve_endpoint_attrs()
            self._build_swargs()
            if not self._swargs:
                raise SWObjectPropertyError("Can't create object without properties.")
            for attr in self._required_swargs_attrs:
                if not getattr(self, attr):
                    raise SWObjectPropertyError(f"Missing required attribute: {attr}")

            self.uri = self.swis.create(self.endpoint, **self._swargs["properties"])
            if self._swargs.get("custom_properties"):
                self.swis.update(
                    f"{self.uri}/CustomProperties",
                    **self._swargs["custom_properties"],
                )
                logger.debug("added custom properties")
            self._init_child_objects()
            self._get_swdata()
            self._get_id()
            self._update_child_attrs()
            self._create_child_objects()
            self.refresh()
            logger.info(f"{self.name}: created {self._type}")
            return True

    def delete(self) -> bool:
        """Delete object"""
        if self.exists():
            self.swis.delete(self.uri)
            self.uri = None
            self.id = None
            self._exists = False
            logger.info(f"{self.name}: deleted {self._type}")
            return True
        else:
            logger.warning(f"{self.name}: {self._type} doesn't exist, doing nothing")
            return False

    def update(self) -> bool:
        """alias to save method, to keep consistent with SWIS verb naming"""
        return self.save()

    def save(self) -> bool:
        """Update object in pysolarwinds with local object's properties"""
        self._resolve_endpoint_attrs()
        self._build_swargs()
        if self.exists():
            if not self._changes:
                self._diff()
            if self._changes:
                if self._changes.get("properties"):
                    self.swis.update(self.uri, **self._changes["properties"])
                    logger.info(
                        f"{self.name}: updated properties: {print_dict(self._changes['properties'])}"
                    )
                    self._get_swdata(refresh=True, data="properties")
                if self._changes.get("custom_properties"):
                    self.swis.update(
                        f"{self.uri}/CustomProperties",
                        **self._changes["custom_properties"],
                    )
                    logger.info(
                        f"{self.name}: updated custom properties: {print_dict(self._changes['custom_properties'])}"
                    )
                    self._get_swdata(refresh=True, data="custom_properties")
                if self._changes.get("child_objects"):
                    logger.debug("found changes to child objects")
                    for attr in self._changes["child_objects"].keys():
                        child = getattr(self, attr)
                        child.save()
                    logger.info(f"{self.name}: updated child objects")
                self._changes = None
                return True
            else:
                logger.info(f"{self.name}: found no changes, doing nothing")
                return False
        else:
            logger.info(f"{self.name}: {self._type} does not exist, creating...")
            return self.create()


class NewEndpoint:
    _entity_type = ""
    _uri_template = ""
    _write_attr_map = {}

    def __init__(
        self,
        swis: SWISClient,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> None:
        self.swis = swis
        self.id = id
        self.uri = uri
        self.data = data
        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)
        if not id and not uri and not data:
            if uri := self._get_uri():
                self.uri = uri
            else:
                raise ValueError("Must provide SWIS ID, URI, or data dict.")
        if not self.uri:
            if id:
                self.uri = self._uri_template.format(self.swis.host, id)
            if data:
                self.uri = self.data.get("Uri")
        if not self.data:
            self.read()

    def _get_uri(self) -> Optional[str]:
        """Subclass-specific method to retrieve URI by other means."""
        pass

    def _read(self) -> dict:
        """Retrieve SWIS info dict."""
        return self.swis.read(self.uri)

    @property
    def description(self) -> str:
        """Description of entity."""
        return self.data.get("Description", "")

    @property
    def details_url(self) -> str:
        """URL for further details."""
        return self.data.get("DetailsUrl", "")

    @property
    def instance_site_id(self) -> str:
        """Unknown meaning."""
        return self.data.get("instanceSiteId", "")

    @property
    def instance_type(self) -> str:
        """Unknown meaning."""
        return self.data.get("InstanceType", "")

    @property
    def name(self) -> str:
        """Override in subclass."""
        return ""

    @property
    def orion_id_column(self) -> str:
        """Unknown meaning."""
        return self.data["OrionIdColumn"]

    @property
    def orion_id_prefix(self) -> str:
        """Unknown meaning."""
        return self.data["OrionIdPrefix"]

    def delete(self) -> None:
        """Delete entity."""
        self.swis.delete(self.uri)

    def read(self) -> None:
        """Update locally cached data about entity."""
        self.data = self._read()

    def save(self) -> None:
        """Save changes, if any, to SWIS."""
        updates = {}
        for attr, prop in self._write_attr_map.items():
            updates.update({prop: getattr(self, attr)})
        self.swis.update(self.uri, **updates)
        logger.debug(f"{self.node}: {self}: updated properties: {updates}")

    def __str__(self) -> str:
        return self.name


class MonitoredEndpoint(NewEndpoint):
    @property
    def avg_response_time(self) -> int:
        """Average response time in milliseconds."""
        return self.data["AvgResponseTime"]

    @property
    def is_unmanaged(self) -> bool:
        """Whether or not node is un-managed."""
        return self.data["UnManaged"]

    @property
    def last_sync(self) -> Optional[datetime.datetime]:
        """Last synchronization with SolarWinds."""
        last_sync = self.data.get("LastSync")
        if last_sync:
            return datetime.datetime.strptime(last_sync, "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def max_response_time(self) -> int:
        """Maximum response time in milliseconds."""
        return self.data["MaxResponseTime"]

    @property
    def min_response_time(self) -> int:
        """Minimum response time in milliseconds."""
        return self.data["MinResponseTime"]

    @property
    def minutes_since_last_sync(self) -> Optional[int]:
        """Minutes since last synchronization with SolarWinds."""
        return self.data.get("MinutesSinceLastSync")

    @property
    def next_poll(self) -> Optional[datetime.datetime]:
        """Next polling date/time."""
        if next_poll := self.data.get("NextPoll"):
            return datetime.datetime.strptime(next_poll, "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def next_rediscovery(self) -> Optional[datetime.datetime]:
        """Next rediscovery date/time."""
        if next_rediscovery := self.data.get("NextRediscovery"):
            return datetime.datetime.strptime(next_rediscovery, "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def percent_loss(self) -> float:
        """Percent packet loss."""
        return self.data["PercentLoss"]

    @property
    def poll_interval(self) -> int:
        """Polling interval in seconds."""
        return self.data["PollInterval"]

    @property
    def rediscovery_interval(self) -> int:
        """Rediscovery interval in seconds."""
        return self.data["RediscoveryInterval"]

    @property
    def response_time(self) -> int:
        """Response time in milliseconds."""
        return self.data["ResponseTime"]

    @property
    def skipped_polling_cycles(self) -> Optional[int]:
        """Number of skipped polling cycles."""
        return self.data.get("SkippedPollingCycles")

    @property
    def stat_collection(self) -> Optional[int]:
        """Unknown meaning."""
        return self.data.get("StatCollection")

    @property
    def status_code(self) -> int:
        """Numeric representation of entity status."""
        return self.data.get("Status")

    @property
    def status_description(self) -> str:
        """Description of status."""
        return self.data.get("StatusDescription", "")

    @property
    def status_icon(self) -> str:
        """Status icon filename."""
        return self.data.get("StatusIcon", "").strip()

    @property
    def status_icon_hint(self) -> str:
        """Status icon hint."""
        return self.data.get("StatusIconHint", "")

    @property
    def status_led(self) -> str:
        """Status LED icon filename."""
        return self.data.get("StatusLED", "").strip()

    @property
    def unmanaged_from(self) -> Optional[datetime.datetime]:
        """Date/time from which the entity will be un-managed."""
        if unmanage_from := self.data.get("UnManageFrom"):
            return datetime.datetime.strptime(unmanage_from, "%Y-%m-%dT%H:%M:%SZ")

    @property
    def unmanaged_until(self) -> Optional[datetime.datetime]:
        """Date/time until which the entity will be un-managed."""
        if unmanage_to := self.data.get("UnManageUntil"):
            return datetime.datetime.strptime(unmanage_to, "%Y-%m-%dT%H:%M:%SZ")
