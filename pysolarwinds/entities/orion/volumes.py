from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from pysolarwinds.entities import MonitoredEntity
from pysolarwinds.list import BaseList
from pysolarwinds.logging import get_logger
from pysolarwinds.queries.orion.volumes import QUERY, TABLE
from pysolarwinds.swis import SWISClient

if TYPE_CHECKING:
    from pysolarwinds.entities.orion.nodes import Node

logger = get_logger(__name__)


class Volume(MonitoredEntity):
    TYPE = "Orion.Volumes"
    WRITE_ATTR_MAP = {}

    def __init__(
        self,
        swis: SWISClient,
        node: Node,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        super().__init__(swis=swis, id=id, uri=uri, data=data)
        self.node = node

    @property
    def _id(self) -> int:
        """Volume ID."""
        return self.volume_id

    @property
    def details_url(self) -> str:
        """Details URL."""
        return self.data.get("DetailsUrl", "")

    @property
    def device_id(self) -> str:
        """Unknown significance."""
        return self.data.get("DeviceId", "")

    @property
    def description(self) -> str:
        """Volume description."""
        return self.data.get("Description", "")

    @property
    def disk_queue_length(self) -> float:
        """Disk queue length. Unknown unit."""
        return self.data["DiskQueueLength"]

    @property
    def disk_reads(self) -> float:
        """Disk reads. Unknown unit."""
        return self.data["DiskReads"]

    @property
    def disk_serial_number(self) -> str:
        """Disk serial number."""
        return self.data.get("DiskSerialNumber", "")

    @property
    def disk_transfer(self) -> float:
        """Disk transfer. Unknown unit."""
        return self.data["DiskTransfer"]

    @property
    def disk_writes(self) -> float:
        return self.data["DiskWrites"]

    @property
    def display_name(self) -> str:
        """Display name."""
        return self.data.get("DisplayName", "")

    @property
    def full_name(self) -> str:
        """Full volume name."""
        return self.data.get("FullName", "")

    @property
    def icon(self) -> str:
        """Volume icon name."""
        return self.data.get("Icon", "")

    @property
    def index(self) -> int:
        """Volume index (likely SNMP OID index)."""
        return self.data["Index"]

    @property
    def interface_type(self) -> str:
        return self.data.get("InterfaceType", "")

    @property
    def name(self) -> str:
        """Voume name."""
        # SWIS will truncate long names in the caption or description fields.
        # The VolumeDescription field is the full, un-truncated name.
        return self.volume_description

    @property
    def node_id(self) -> int:
        """Volume's parent node ID."""
        return self.data["NodeID"]

    @property
    def instance_type(self) -> str:
        """Instance type. Unknown meaning."""
        return self.data.get("InstanceType", "")

    @property
    def instance_site_id(self) -> Optional[bool]:
        """Unknown meaning."""
        return self.data.get("InstanceSiteId")

    @property
    def is_responding(self) -> bool:
        """Whether disk is responding."""
        return self.data.get("Responding") == "Y"

    @property
    def iops(self) -> Optional[float]:
        """Convenience alias."""
        return self.total_disk_iops

    @property
    def orion_id_colum(self) -> str:
        """Unknown meaning."""
        return self.data.get("OrionIdColumn", "")

    @property
    def orion_id_prefix(self) -> str:
        """Unknown meaning."""
        return self.data.get("OrionIdPrefix", "")

    @property
    def percent_available(self) -> Optional[float]:
        """Convenience alias."""
        return self.volume_percent_available

    @property
    def percent_used(self) -> Optional[float]:
        """Convenience alias."""
        return self.volume_percent_used

    @property
    def scsi_controller_id(self) -> str:
        """SCSI controller ID."""
        return self.data.get("SCSIControllerId", "")

    @property
    def scsi_lun_id(self) -> Optional[int]:
        """SCSI LUN ID."""
        return self.data.get("SCSILunId")

    @property
    def scsi_port_id(self) -> Optional[int]:
        """SCSI port ID."""
        return self.data.get("SCSIPortId")

    @property
    def scsi_port_offset(self) -> Optional[int]:
        """SCSI port offset."""
        return self.data.get("SCSIPortOffset")

    @property
    def scsi_target_id(self) -> Optional[int]:
        """SCSI target ID."""
        return self.data.get("SCSITargetId")

    @property
    def size(self) -> Optional[float]:
        """Volume size. Unknown unit."""
        return self.data.get("Size")

    @property
    def space_available(self) -> Optional[float]:
        """Convenience alias."""
        return self.volume_space_available

    @property
    def space_used(self) -> Optional[float]:
        """Convenience alias."""
        return self.volume_space_used

    @property
    def total_disk_iops(self) -> Optional[float]:
        """Total disk input/output operations per second."""
        return self.data.get("TotalDiskIOPS")

    @property
    def type(self) -> str:
        """Volume type."""
        return self.data.get("Type", "")

    @property
    def volume_allocation_failures_this_hour(self) -> Optional[int]:
        """Volume allocation failures in the last 60 minutes."""
        return self.data.get("VolumeAllocationFailuresThisHour")

    @property
    def volume_allocation_failures_today(self) -> Optional[int]:
        """Volume allocation failures in the last 24 hours."""
        return self.data.get("VolumeAllocationFailuresToday")

    @property
    def volume_description(self) -> str:
        """Volume description."""
        return self.data["VolumeDescription"] or ""

    @property
    def volume_id(self) -> int:
        """Volume ID."""
        return self.data["VolumeID"]

    @property
    def volume_index(self) -> Optional[int]:
        """Volume index. Unknown significance."""
        return self.data.get("VolumeIndex")

    @property
    def volume_percent_available(self) -> Optional[float]:
        """Percent available."""
        return self.data.get("VolumePercentAvailable")

    @property
    def volume_percent_used(self) -> Optional[float]:
        """Percent used."""
        return self.data.get("VolumePercentUsed")

    @property
    def volume_responding(self) -> bool:
        """Whether the volume is responding."""
        return self.data.get("VolumeResponding") == "Y"

    @property
    def volume_size(self) -> Optional[float]:
        """Volume size. Unknown unit."""
        return self.data.get("VolumeSize")

    @property
    def volume_space_available(self) -> Optional[float]:
        """Volume space available, likely in kilobytes."""
        return self.data.get("VolumeSpaceAvailable")

    @property
    def volume_space_available_exp(self) -> Optional[float]:
        """Volume space available in an unknown unit."""
        return self.data.get("VolumeSpaceAvailableExp")

    @property
    def volume_space_used(self) -> Optional[float]:
        """Volume space used, likely in kilobytes."""
        return self.data.get("VolumeSpaceUsed")

    @property
    def volume_type(self) -> str:
        """Volume type."""
        return self.data.get("VolumeType") or ""

    @property
    def volume_type_id(self) -> Optional[int]:
        """Unknown meaning."""
        return self.data.get("VolumeTypeID")

    @property
    def volume_type_icon(self) -> str:
        """Volume type icon string."""
        return self.data.get("VolumeTypeIcon") or ""

    def delete(self) -> None:
        """Delete volume."""
        self.swis.delete(self.uri)
        if self.node.volumes.get(self):
            self.node.volumes.items.remove(self)
        logger.info("Deleted volume.")

    def __repr__(self) -> str:
        return f'Volume("{self.name}")'


class VolumeList(BaseList):
    _item_class = Volume

    def delete(self, volumes: Union[Volume, list[Volume]]) -> None:
        """Delete one or more volumes.

        Args:
            volumes: A `Volume` or list of `Volume`s to delete.

        Returns:
            None.

        Raises:
            None.
        """
        if isinstance(volumes, list):
            self.swis.delete([x.uri for x in volumes])
            for volume in volumes:
                self.node.volumes.items.remove(volume)
            logger.info(f"Deleted {len(volumes)} volumes.")
        else:
            volumes.delete()

    def delete_all(self) -> None:
        """Delete all volumes."""
        self.fetch()
        volume_count = len(self)
        if volume_count:
            self.swis.delete([x.uri for x in self])
            self.items = []
            logger.info(f"Deleted all volumes ({volume_count}).")
        else:
            logger.info("No volumes to delete.")

    def fetch(self) -> None:
        """Fetch all volumes."""
        query = QUERY.where(TABLE.NodeID == self.node.id)
        if results := self.swis.query(str(query)):
            self.items = [
                Volume(swis=self.swis, node=self.node, data=x) for x in results
            ]

    def __repr__(self) -> str:
        return super().__repr__()
