import logging
from pprint import pprint

import ipdb
import solarwinds

from config import snmpv2c, sw_args

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**sw_args)

node = sw.orion.nodes.node(ip_address="10.12.104.97")
node.get()
ipdb.set_trace()
