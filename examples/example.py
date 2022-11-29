import logging

import ipdb
from config import SW_ARGS
from rich import print

import solarwinds

disable_loggers = [
    "asyncio",
    "httpx._client"
]
for logger in disable_loggers:
    logging.getLogger(logger).disabled = True

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(name)s.%(funcName)s:%(lineno)d]  %(msg)s",
)

sw = solarwinds.api(**SW_ARGS)


# node = sw.orion.node(
#     caption="death-star",
#     snmpv3_ro_cred=sw.orion.credential(name="NETSEC"),
#     custom_properties={"Site": "PTC - Plano, TX, US", "Region": "AMER"},
# )
node = sw.orion.node(
    **{
        "caption": "FBDR00FW01",
        "ip_address": "172.25.133.5",
        "polling_method": "icmp",
        "snmp_version": 0,
        "snmpv2c_ro_community": None,
        "snmpv2c_rw_community": None,
        "engine_id": 1,
        "custom_properties": {
            "Region": "EMEA",
            "Site": "BDR - Equinix FR5 - Frankfurt, DE",
        },
        "latitude": 50.098897,
        "longitude": 8.632206,
    }
)
# cred = sw.orion.credential(id=10)
# node.update()
# node.snmp_version = 3
# node.snmpv3_ro_cred = cred
# node.update()
# node.create()
ipdb.set_trace()
