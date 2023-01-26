from typing import Dict, List, Optional, Union

from solarwinds.api import API
from solarwinds.endpoint import NewEndpoint
from solarwinds.exceptions import SWObjectExists
from solarwinds.list import BaseList
from solarwinds.logging import get_logger

logger = get_logger(__name__)


class OrionVolume(NewEndpoint):
    _entity_type = "Orion.Volumes"
    _write_attr_map = {}

    def __init__(
        self,
        api: API,
        node,
        data: Optional[Dict] = None,
        uri: Optional[str] = None,
    ) -> None:
        super().__init__(api=api, data=data, uri=uri)
        self.node = node

    @property
    def id(self) -> int:
        return self.volume_id

    @property
    def display_name(self) -> Optional[str]:
        return self.data.get("DisplayName")

    @property
    def description(self) -> Optional[str]:
        return self.data.get("Description")

    @property
    def name(self) -> str:
        return self.display_name

    @property
    def volume_id(self) -> int:
        return self.data.get("VolumeID")

    @property
    def instance_type(self) -> str:
        return self.data.get("InstanceType")

    @property
    def instance_site_id(self) -> bool:
        return self.data.get("InstanceSiteId")

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
