import logging

import ipdb
import solarwinds
from rich import print

from config import SNMPV2C, SW_ARGS

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**SW_ARGS)


node = sw.orion.node(caption="death-star", snmpv3_cred_name="NETSEC")
ipdb.set_trace()
