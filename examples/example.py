import logging

import ipdb
import solarwinds
from rich import print

from config import SW_ARGS

disable_loggers = ["asyncio", "httpx._client"]
for logger in disable_loggers:
    logging.getLogger(logger).disabled = True

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s [%(name)s.%(funcName)s:%(lineno)d]  %(msg)s",
)

sw = solarwinds.api(**SW_ARGS)


node = sw.orion.node(
    caption="death-star",
    snmpv3_ro_cred=sw.orion.credential(name="NETSEC"),
    custom_properties={"Site": "PTC - Plano, TX, US", "Region": "AMER"},
)

# node.update()
# node.snmp_version = 3
# node.snmpv3_ro_cred = cred
# node.update()
ipdb.set_trace()
