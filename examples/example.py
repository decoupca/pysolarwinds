import logging

import ipdb
import solarwinds
from rich import print

from config import SNMPV2C, SW_ARGS

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**SW_ARGS)


node = sw.orion.node(ip_address="172.25.46.14")
ipdb.set_trace()
