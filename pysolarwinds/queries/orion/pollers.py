"""Poller query."""
from pypika import MSSQLQuery, Table

TABLE = Table("Orion.Nodes")
FIELDS = (
    "PollerID",
    "PollerType",
    "NetObject",
    "NetObjectType",
    "NetObjectID",
    "Enabled",
    "DisplayName",
    "Description",
    "InstanceType",
    "Uri",
    "InstanceSiteId",
)
QUERY = MSSQLQuery.from_(TABLE).select(*FIELDS)
