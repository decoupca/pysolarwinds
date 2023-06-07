from pypika import MSSQLQuery, Table

TABLE = Table("Orion.WorldMap.Point")
FIELDS = (
    "PointId",
    "Instance",
    "InstanceID",
    "Latitude",
    "Longitude",
    "AutoAdded",
    "StreetAddress",
    "DisplayName",
    "Description",
    "InstanceType",
    "Uri",
    "InstanceSiteId",
)
QUERY = MSSQLQuery.from_(TABLE).select(*FIELDS)
