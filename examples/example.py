import logging

import ipdb
from config import SNMPV2C, SW_ARGS
from rich import print

import solarwinds

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
node = sw.orion.node(caption="RAPC00ED11")
# node.intfs.discover()
ipdb.set_trace()
