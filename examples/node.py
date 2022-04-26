import logging
from pprint import pprint

import ipdb
import solarwinds

from config import snmpv2c, sw_args

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**sw_args)

node = sw.orion.nodes.node(ipaddress="10.12.104.97")
node.get()
node.map_point.get()
ipdb.set_trace()
