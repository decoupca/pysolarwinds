import json
import re
from typing import Union
from solarwinds.endpoint import Endpoint
from solarwinds.logging import log




def invoke(self, entity, verb, *args):
    url = f"{c.SW_API_URL}/Invoke/{entity}/{verb}"
    response = self.http_client.post(url, data=json.dumps(args))
    if 400 <= response.status_code < 600:
        try:
            log.debug(json.loads(response.text)["Message"])
        except:
            pass
    response.raise_for_status()
    return response.json()


class OrionInterface(Endpoint):
    endpoint = "Orion.NPM.Interfaces"

    def __init__(self, device, data: dict):
        self.device = device
        self.data = data
        self._id = None
        self._name = None
        self._mtu = None
        self._mac_address = None
        self._duplex = None
        self._oper_status = None
        self._admin_status = None
        self._speed = None
        for k, v in data.items():
            setattr(self, f"_{k}", v)

    @property
    def id(self) -> int:
        return int(self._id)

    @property
    def name(self) -> str:
        return self._name.strip()

    @property
    def mtu(self) -> int:
        return int(self.mtu)

    @property
    def mac_address(self) -> str:
        return self._mac_address

    @property
    def duplex(self) -> str:
        return self._duplex

    @property
    def enabled(self) -> bool:
        return self._admin_status == 1

    @property
    def disabled(self) -> bool:
        return self.enabled is False

    @property
    def up(self) -> bool:
        return self._oper_status == 1

    @property
    def down(self) -> bool:
        return self.up is False

    @property
    def speed(self) -> int:
        return int(self._speed)

    def __repr__(self) -> str:
        return self.name


class OrionInterfaces(object):
    endpoint = "Orion.NPM.Interfaces"

    def __init__(self, device) -> None:
        self.device = device
        self.swis = device.swis
        self._existing_interfaces = None
        self._discovered_interfaces = None

    def _get_iface_by_abbr(self, abbr):
        abbr = abbr.lower()
        abbr_pattern = r"^([a-z\-]+)([\d\/\:]+)$"
        match = re.match(abbr_pattern, abbr)
        if match:
            begin = match.group(1)
            end = match.group(2)
            full_pattern = re.compile(f"^{begin}[a-z\-]+{end}$", re.I)
            matches = []
            for iface in self._existing_interfaces:
                if re.match(full_pattern, iface.name):
                    matches.append(iface)
            if len(matches) == 0:
                raise IndexError(f"no matches found: {abbr}")
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise IndexError(f"ambiguous reference: {abbr}")
        else:
            raise IndexError

    def add(self, interfaces):
        return invoke(
            "Orion.NPM.Interfaces",
            "AddInterfacesOnNode",
            self.device.id,
            interfaces,
            "AddDefaultPollers",
        )

    def get(self) -> None:
        """
        Queries for interfaces that have already been discovered and assigned
        to device
        """
        log.info(f"{self.device.name}: getting existing interfaces...")
        query = f"""
            SELECT
                I.AdminStatus AS admin_status,
                I.InterfaceID AS id,
                I.InterfaceName AS name,
                I.MTU AS mtu,
                I.OperStatus AS oper_status,
                I.PhysicalAddress AS mac_address,
                I.Speed AS speed
            FROM
                Orion.Nodes N
            JOIN
                Orion.NPM.Interfaces I ON N.NodeID = I.NodeID
            WHERE
                N.NodeID = '{self.device.id}'
        """
        result = self.swis.query(query)["results"]
        self._existing_interfaces = [
            OrionInterface(self.device, data=data) for data in result
        ]
        log.info(
            f"{self.device.name}: found {len(self._existing_interfaces)} existing interfaces"
        )

    def discover(self) -> None:
        """
        Runs SNMP discovery of all available interfaces
        This can take a long time
        """
        log.info(f"{self.device.name}: discovering interfaces via SNMP...")
        result = self.swis.invoke(
            "Orion.NPM.Interfaces", "DiscoverInterfacesOnNode", self.device.id
        )
        log.info(
            f"{self.device.name}: discovered {len(self._discovered_interfaces)} interfaces"
        )
        self._discovered_interfaces = result["DiscoveredInterfaces"]

    def monitor(self, interfaces=None) -> None:
        if self._existing_interfaces is None:
            self.get()
        if interfaces is None:
            interfaces = self._existing_interfaces

        existing = [x.name for x in self._existing_interfaces]
        missing = [x for x in interfaces if x not in existing]

        # if there are any interfaces we want to monitor that don't already exist,
        # we need to run a full snmp discovery
        needs_discovery = bool(missing)
        if needs_discovery is True:
            self.discover()
            add = [
                x
                for x in self._discovered_interfaces
                if x["Caption"].split(" ")[0] in missing
            ]
            log.info(f"{self.device.name}: found {len(add)} interfaces to monitor")
            if add:
                self.add(add)
        else:
            log.info(
                f"{self.device.name}: all interfaces already monitored, doing nothing"
            )

    def __getitem__(self, item: Union[str, int]) -> OrionInterface:
        if isinstance(item, int):
            return self._existing_interfaces[item]
        else:
            try:
                result = [
                    x
                    for x in self._existing_interfaces
                    if x.name.lower() == item.lower()
                ][0]
            except IndexError:
                result = self._get_iface_by_abbr(item)
            return result

    def __repr__(self) -> str:
        if self._existing_interfaces is None:
            self.get()
        return str(self._existing_interfaces)
