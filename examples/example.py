import solarwinds

from pprint import pprint

import ipdb
from config import sw_args, snmpv2c
import logging

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**sw_args)

# node = sw.node(
#    ip="172.16.1.1",
#    hostname="Cantina",
#    # properties={'EngineID': 2},
#    custom_properties={"Site": "Mos Eisley", "Region": "Tatooine"},
# )


node = sw.orion.nodes.node(ip="10.12.104.97", snmpv2c=snmpv2c)
point = sw.orion.worldmap.point(instance_id=799)
print(point.get_uri())

ipdb.set_trace()
