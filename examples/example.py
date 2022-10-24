import logging

import ipdb
import solarwinds
from rich import print

from config import SNMPV2C, SW_ARGS

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**SW_ARGS)


# node = sw.orion.node(
#     ip_address="172.25.46.14",
#     snmpv3_ro_cred_name="NETSEC",
#     custom_properties={"Site": "PTC - Plano, TX, US", "Region": "AMER"},
# )
# node.update()
host = "FAPC00FW21"
node = sw.orion.node(caption=host)
cred = sw.orion.credential(name="blah")
node.snmp_version = 3
node.settings.snmpv3_ro_cred = cred
node.update()
# node.settings.snmpv3_ro_cred = cred

ipdb.set_trace()
