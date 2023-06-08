import datetime
from typing import Optional

from pysolarwinds.defaults import EXCLUDE_CUSTOM_PROPS
from pysolarwinds.exceptions import (
    SWIDNotFoundError,
    SWObjectExistsError,
    SWObjectPropertyError,
)
from pysolarwinds.logging import get_logger
from pysolarwinds.swis import SWISClient

logger = get_logger(__name__)


class Entity:
    TYPE = ""
    URI_TEMPLATE = ""
    WRITE_ATTR_MAP = {}

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
        self.uri = uri or ""
        self.data = data or {}
        self.custom_properties = {}
        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)
        if not id and not uri and not data:
            if data := self._get_data():
                self.data = data
            else:
                msg = "Must provide SWIS ID, URI, or data dict."
                raise ValueError(msg)
        if not self.uri:
            if id:
                self.uri = self.URI_TEMPLATE.format(self.swis.host, id)
            if data:
                self.uri = self.data.get("Uri")
        if not self.data:
            self.read()
        if not self.id:
            self.id = self._id

    def _get_data(self) -> Optional[dict]:
        """Subclass-specific method to retrieve data by other means."""

    def _read(self) -> dict:
        """Retrieve SWIS info dict."""
        return self.swis.read(self.uri)

    @property
    def description(self) -> str:
        """Description of entity."""
        return self.data.get("Description", "")

    @property
    def _id(self) -> int:
        """Retrieve entity ID from data dict."""

    @property
    def cp(self) -> dict:
        """Convenience alias."""
        return self.custom_properties

    def delete(self) -> None:
        """Delete entity."""
        self.swis.delete(self.uri)

    def read(self) -> None:
        """Update locally cached data about entity."""
        self.data = self._read()

    def save(self, updates: dict = {}) -> None:
        """Save changes, if any, to SWIS."""
        if not updates:
            for attr, prop in self.WRITE_ATTR_MAP.items():
                attr_val = getattr(self, attr)
                prop_val = self.data[prop]
                if attr_val != prop_val:
                    updates.update({prop: attr_val})
        if updates:
            self.swis.update(self.uri, **updates)
            for attr, key in self.WRITE_ATTR_MAP.items():
                value = getattr(self, attr)
                self.data[key] = value
            logger.debug(f"Updated properties: {updates}")
        else:
            logger.debug("Nothing to update.")
        if hasattr(self, "custom_properties"):
            self.custom_properties.save()

    def __str__(self) -> str:
        return self.name


class MonitoredEntity(Entity):
    @property
    def avg_response_time(self) -> int:
        """Average response time in milliseconds."""
        return self.data["AvgResponseTime"]

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
    def is_unmanaged(self) -> bool:
        """Whether or not node is un-managed."""
        return self.data["UnManaged"]

    @property
    def last_sync(self) -> Optional[datetime.datetime]:
        """Last synchronization with SolarWinds."""
        if last_sync := self.data.get("LastSync"):
            return datetime.datetime.strptime(last_sync, "%Y-%m-%dT%H:%M:%S.%f")
        return None

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
        return None

    @property
    def next_rediscovery(self) -> Optional[datetime.datetime]:
        """Next rediscovery date/time."""
        if next_rediscovery := self.data.get("NextRediscovery"):
            return datetime.datetime.strptime(next_rediscovery, "%Y-%m-%dT%H:%M:%S.%f")
        return None

    @property
    def orion_id_column(self) -> str:
        """Unknown meaning."""
        return self.data.get("OrionIdColumn", "")

    @property
    def orion_id_prefix(self) -> str:
        """Unknown meaning."""
        return self.data.get("OrionIdPrefix", "")

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
        return None

    @property
    def unmanaged_until(self) -> Optional[datetime.datetime]:
        """Date/time until which the entity will be un-managed."""
        if unmanage_to := self.data.get("UnManageUntil"):
            return datetime.datetime.strptime(unmanage_to, "%Y-%m-%dT%H:%M:%SZ")
        return None
