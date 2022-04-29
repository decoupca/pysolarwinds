import logging
from pprint import pprint

import ipdb
import solarwinds

from config import snmpv2c, sw_args

format = '%(asctime)s %(levelname)s %(funcName)s %(lineno)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=format)

sw = solarwinds.api(**sw_args)
#node_args = {'caption': 'death-star', 'ip_address': '172.16.1.1', 'community': '3!3ph4n!', 'rw_community': '1a6dr0v3r', 'engine_id': 1, 'custom_properties': {'Region': 'AMER', 'Site': 'WTC - MIS - New York, NY'}, 'latitude': 40.713608, 'longitude': -74.012143}
#node = sw.orion.nodes.node(**node_args)
#node = sw.orion.nodes.node(caption='RBFT08IN01', community='3!3ph4n!')
node = sw.orion.nodes.node(caption='death-star')
ipdb.set_trace()
