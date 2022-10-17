import logging

import ipdb
from config import SNMPV2C, SW_ARGS
from rich import print

import solarwinds

logging.basicConfig(level=logging.DEBUG)

sw = solarwinds.api(**SW_ARGS)


# node = sw.orion.node(
#     ip_address="172.25.46.14",
#     snmpv3_cred_name="NETSEC",
#     custom_properties={"Site": "PTC - Plano, TX, US", "Region": "AMER"},
# )
# node.update()
host = "FTC-OBLBNADM901"
node = sw.orion.node(caption=host)
node.snmp_version = 3
node.snmpv3_cred_name = "NETSEC"
# node.update()

ipdb.set_trace()
