import solarwinds

from pprint import pprint

import ipdb
from config import sw_args


sw = solarwinds.api(**sw_args)

node = sw.node(
    ip="172.16.1.1",
    hostname="Cantina",
    # properties={'EngineID': 2},
    custom_properties={"site": "Mos Eisley", "region": "Tatooine"},
)
ipdb.set_trace()
