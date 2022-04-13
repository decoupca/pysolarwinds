from pprint import pprint

import ipdb
from config import sw_args

from pysolarwinds import Solarwinds

sw = Solarwinds(**sw_args)

node = sw.node(
    ip="172.16.1.1",
    hostname="Cantina",
    custom_properties={"site": "Mos Eisley", "region": "Tatooine"},
)
ipdb.set_trace()
