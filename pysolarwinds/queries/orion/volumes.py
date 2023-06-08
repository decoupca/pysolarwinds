"""Volume query."""
from pypika import MSSQLQuery, Table

TABLE = Table("Orion.Volumes")
FIELDS = (
    "AncestorDetailsUrls",
    "AncestorDisplayNames",
    "Caption",
    "Description",
    "DetailsUrl",
    "DeviceId",
    "DiskQueueLength",
    "DiskReads",
    "DiskSerialNumber",
    "DiskTransfer",
    "DiskWrites",
    "DisplayName",
    "FullName",
    "Icon",
    "Image",
    "Index",
    "InstanceSiteId",
    "InstanceType",
    "InterfaceType",
    "LastSync",
    "MinutesSinceLastSync",
    "NextPoll",
    "NextRediscovery",
    "NodeID",
    "OrionIdColumn",
    "OrionIdPrefix",
    "PollInterval",
    "RediscoveryInterval",
    "Responding",
    "SCSIControllerId",
    "SCSILunId",
    "SCSIPortId",
    "SCSIPortOffset",
    "SCSITargetId",
    "Size",
    "SkippedPollingCycles",
    "StatCollection",
    "Status",
    "StatusDescription",
    "StatusIcon",
    "StatusIconHint",
    "StatusLED",
    "TotalDiskIOPS",
    "Type",
    "UnManageFrom",
    "UnManageUntil",
    "UnManaged",
    "Uri",
    "VolumeAllocationFailuresThisHour",
    "VolumeAllocationFailuresToday",
    "VolumeDescription",
    "VolumeID",
    "VolumeIndex",
    "VolumePercentAvailable",
    "VolumePercentUsed",
    "VolumeResponding",
    "VolumeSize",
    "VolumeSpaceAvailable",
    "VolumeSpaceAvailableExp",
    "VolumeSpaceUsed",
    "VolumeType",
    "VolumeTypeID",
    "VolumeTypeIcon",
)
QUERY = MSSQLQuery.from_(TABLE).select(*FIELDS)
