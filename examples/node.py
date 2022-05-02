import logging
from pprint import pprint

import ipdb
from config import snmpv2c, sw_args

import solarwinds

format = "%(asctime)s %(levelname)s %(funcName)s %(lineno)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=format)

sw = solarwinds.api(**sw_args)
# node_args = {'caption': 'death-star', 'ip_address': '172.16.1.1', 'community': '3!3ph4n!', 'rw_community': '1a6dr0v3r', 'engine_id': 1, 'custom_properties': {'Region': 'AMER', 'Site': 'WTC - MIS - New York, NY'}, 'latitude': 40.713608, 'longitude': -74.012143}
# node = sw.orion.node(**node_args)
# node = sw.orion.node(caption='RBFT08IN01', community='3!3ph4n!')
# node = sw.orion.node(caption="RBFT08IN01")
node = sw.orion.node(ip_address="172.25.84.11")
ipdb.set_trace()
