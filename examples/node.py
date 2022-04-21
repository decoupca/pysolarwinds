import solarwinds

from pprint import pprint

import ipdb
from config import sw_args
import logging

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**sw_args)

# node = sw.node(
#    ip="172.16.1.1",
#    hostname="Cantina",
#    # properties={'EngineID': 2},
#    custom_properties={"Site": "Mos Eisley", "Region": "Tatooine"},
# )


node = sw.node(ip="10.12.104.97")

ipdb.set_trace()
