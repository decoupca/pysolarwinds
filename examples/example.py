import logging

import ipdb
import solarwinds
from rich import print

from config import SNMPV2C, SW_ARGS

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**SW_ARGS)

# node = sw.node(
#    ip="172.16.1.1",
#    hostname="Cantina",
#    # properties={'EngineID': 2},
#    custom_properties={"Site": "Mos Eisley", "Region": "Tatooine"},
# )


# node = sw.orion.nodes.node(ip="10.12.104.97", snmpv2c=snmpv2c)
# point = sw.orion.worldmap.point(instance_id=799)
# point2 = sw.orion.worldmap.point()
# point2.instance_id = 800
# point2.get()
node = sw.orion.node(caption="RBCF17CR01-U1")
intfs = [
    "TenGigabitEthernet1/1/3",
    "TenGigabitEthernet2/1/3",
    "Tunnel3",
    "Tunnel4",
    "Tunnel5",
    "Tunnel6",
    "Tunnel7",
    "GigabitEthernet1/0/1",
    "TenGigabitEthernet1/1/1",
    "GigabitEthernet2/0/1",
    "TenGigabitEthernet2/1/1",
    "Loopback0",
    "Vlan203",
    "Vlan213",
    "Loopback100",
    "Loopback101",
    "Vlan200",
    "Vlan3153",
    "Vlan3160",
    "Vlan3105",
    "Port-channel10",
    "Capwap0",
    "Capwap1",
    "Capwap2",
    "Capwap3",
    "Vlan1100",
    "Vlan3152",
    "Vlan1500",
    "Vlan3155",
    "Vlan1300",
    "Vlan1700",
    "Vlan3100",
    "Vlan3102",
    "Vlan3103",
    "Vlan3104",
    "Vlan3107",
    "Vlan3108",
    "Vlan3150",
    "Vlan3151",
    "Vlan3154",
    "Vlan1212",
    "Vlan1222",
    "Vlan1217",
    "Vlan1227",
]
node.intfs.monitor(intfs)
ipdb.set_trace()
