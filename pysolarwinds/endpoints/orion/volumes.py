from typing import Dict, List, Optional, Union

from pysolarwinds.swis import SWISClient
from pysolarwinds.endpoint import MonitoredEndpoint
from pysolarwinds.exceptions import SWObjectExists
from pysolarwinds.list import BaseList
from pysolarwinds.logging import get_logger

logger = get_logger(__name__)


class OrionVolume(MonitoredEndpoint):
    _entity_type = "Orion.Volumes"
    _write_attr_map = {}

    def __init__(
        self,
        swis: SWISClient,
        node,
        data: Optional[Dict] = None,
        uri: Optional[str] = None,
    ) -> None:
        super().__init__(swis=swis, data=data, uri=uri)
        self.node = node

    @property
    def details_url(self) -> str:
        return self.data.get("DetailsUrl") or ""

    @property
    def device_id(self) -> str:
        return self.data.get("DeviceId") or ""

    @property
    def description(self) -> str:
        return self.data.get("Description") or ""

    @property
    def device_id(self) -> str:
        return self.data.get("DeviceId") or ""

    @property
    def disk_queue_length(self) -> Optional[float]:
        return self.data.get("DiskQueueLength")

    @property
    def disk_reads(self) -> Optional[float]:
        return self.data.get("DiskReads")

    @property
    def disk_serial_number(self) -> str:
        return self.data.get("DiskSerialNumber") or ""

    @property
    def disk_transfer(self) -> Optional[float]:
        return self.data.get("DiskTransfer")

    @property
    def disk_writes(self) -> Optional[float]:
        return self.data.get("DiskWrites")

    @property
    def display_name(self) -> str:
        return self.data.get("DisplayName") or ""

    @property
    def full_name(self) -> str:
        return self.data.get("FullName") or ""

    @property
    def icon(self) -> str:
        return self.data.get("Icon") or ""

    @property
    def index(self) -> Optional[int]:
        return self.data.get("Index")

    @property
    def interface_type(self) -> str:
        return self.data.get("InterfaceType") or ""

    @property
    def id(self) -> int:
        return self.volume_id

    @property
    def name(self) -> str:
        # SWIS will truncate long names in the caption or description fields.
        # The VolumeDescription field is the full, un-truncated name.
        return self.volume_description

    @property
    def node_id(self) -> Optional[int]:
        return self.data.get("NodeID")

    @property
    def instance_type(self) -> str:
        return self.data.get("InstanceType") or ""

    @property
    def instance_site_id(self) -> Optional[bool]:
        return self.data.get("InstanceSiteId")

    @property
    def is_responding(self) -> bool:
        return self.data.get("Responding") == "Y"

    @property
    def iops(self) -> bool:
        """Convenience alias"""
        return self.total_disk_iops

    @property
    def orion_id_colum(self) -> str:
        return self.data.get("OrionIdColumn") or ""

    @property
    def orion_id_prefix(self) -> str:
        return self.data.get("OrionIdPrefix") or ""

    @property
    def percent_available(self) -> Optional[float]:
        """Convenience alias"""
        return self.volume_percent_available

    @property
    def percent_used(self) -> Optional[float]:
        """Convenience alias"""
        return self.volume_percent_used

    @property
    def scsi_controller_id(self) -> str:
        return self.data.get("SCSIControllerId") or ""

    @property
    def scsi_lun_id(self) -> Optional[int]:
        return self.data.get("SCSILunId")

    @property
    def scsi_port_id(self) -> Optional[int]:
        return self.data.get("SCSIPortId")

    @property
    def scsi_port_offset(self) -> Optional[int]:
        return self.data.get("SCSIPortOffset")

    @property
    def scsi_target_id(self) -> Optional[int]:
        return self.data.get("SCSITargetId")

    @property
    def size(self) -> Optional[float]:
        return self.data.get("Size")

    @property
    def space_available(self) -> Optional[float]:
        """Convenience alias"""
        return self.volume_space_available

    @property
    def space_used(self) -> Optional[float]:
        """Convenience alias"""
        return self.volume_space_used

    @property
    def total_disk_iops(self) -> Optional[float]:
        return self.data.get("TotalDiskIOPS")

    @property
    def type(self) -> str:
        return self.data.get("Type") or ""

    @property
    def volume_allocation_failures_this_hour(self) -> Optional[int]:
        return self.data.get("VolumeAllocationFailuresThisHour")

    @property
    def volume_allocation_failures_today(self) -> Optional[int]:
        return self.data.get("VolumeAllocationFailuresToday")

    @property
    def volume_description(self) -> str:
        return self.data["VolumeDescription"] or ""

    @property
    def volume_id(self) -> Optional[int]:
        return self.data.get("VolumeID")

    @property
    def volume_index(self) -> Optional[int]:
        return self.data.get("VolumeIndex")

    @property
    def volume_percent_available(self) -> Optional[float]:
        return self.data.get("VolumePercentAvailable")

    @property
    def volume_percent_used(self) -> Optional[float]:
        return self.data.get("VolumePercentUsed")

    @property
    def volume_responding(self) -> bool:
        return self.data.get("VolumeResponding") == "Y"

    @property
    def volume_size(self) -> Optional[float]:
        return self.data.get("VolumeSize")

    @property
    def volume_space_available(self) -> Optional[float]:
        return self.data.get("VolumeSpaceAvailable")

    @property
    def volume_space_available_exp(self) -> Optional[float]:
        return self.data.get("VolumeSpaceAvailableExp")

    @property
    def volume_space_used(self) -> Optional[float]:
        return self.data.get("VolumeSpaceUsed")

    @property
    def volume_type(self) -> str:
        return self.data.get("VolumeType") or ""

    @property
    def volume_type_id(self) -> Optional[int]:
        return self.data.get("VolumeTypeID")

    @property
    def volume_type_icon(self) -> str:
        return self.data.get("VolumeTypeIcon") or ""

    def delete(self) -> bool:
        self.api.delete(self.uri)
        if self.node.volumes.get(self):
            self.node.volumes.items.remove(self)
        logger.info(f"{self.node}: {self}: deleted volume")
        return True

    def __repr__(self) -> str:
        return f'OrionVolume("{self.name}")'


class OrionVolumes(BaseList):
    _item_class = OrionVolume

    def delete(self, volumes: Union[OrionVolume, List[OrionVolume]]) -> bool:
        if isinstance(volumes, list):
            self.api.delete([x.uri for x in volumes])
            for volume in volumes:
                self.node.volumes.items.remove(volume)
            logger.info(f"{self.node}: deleted {len(volumes)} volumes")
        else:
            volume.delete()
        return True

    def delete_all(self) -> bool:
        self.fetch()
        volume_count = len(self)
        if volume_count:
            self.api.delete([x.uri for x in self])
            self.items = []
            logger.info(f"{self.node}: Deleted all volumes ({volume_count})")
            return True
        else:
            logger.info(f"{self.node}: No volumes to delete")
            return False

    def fetch(self) -> None:
        query = f"""
            SELECT
                AncestorDetailsUrls,
                AncestorDisplayNames,
                Caption,
                Description,
                DetailsUrl,
                DeviceId,
                DiskQueueLength,
                DiskReads,
                DiskSerialNumber,
                DiskTransfer,
                DiskWrites,
                DisplayName,
                FullName,
                Icon,
                Image,
                Index,
                InstanceSiteId,
                InstanceType,
                InterfaceType,
                LastSync,
                MinutesSinceLastSync,
                NextPoll,
                NextRediscovery,
                NodeID,
                OrionIdColumn,
                OrionIdPrefix,
                PollInterval,
                RediscoveryInterval,
                Responding,
                SCSIControllerId,
                SCSILunId,
                SCSIPortId,
                SCSIPortOffset,
                SCSITargetId,
                Size,
                SkippedPollingCycles,
                StatCollection,
                Status,
                StatusDescription,
                StatusIcon,
                StatusIconHint,
                StatusLED,
                TotalDiskIOPS,
                Type,
                UnManageFrom,
                UnManageUntil,
                UnManaged,
                Uri,
                VolumeAllocationFailuresThisHour,
                VolumeAllocationFailuresToday,
                VolumeDescription,
                VolumeID,
                VolumeIndex,
                VolumePercentAvailable,
                VolumePercentUsed,
                VolumeResponding,
                VolumeSize,
                VolumeSpaceAvailable,
                VolumeSpaceAvailableExp,
                VolumeSpaceUsed,
                VolumeType,
                VolumeTypeID,
                VolumeTypeIcon
            FROM Orion.Volumes
            WHERE NodeID = '{self.node.id}'
        """
        results = self.api.query(query)
        if results:
            volumes = []
            for result in results:
                volumes.append(OrionVolume(api=self.api, node=self.node, data=result))
            self.items = volumes
