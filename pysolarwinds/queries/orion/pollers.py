from pypika import MSSQLQuery, Table

TABLE = Table("Orion.Pollers")
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
