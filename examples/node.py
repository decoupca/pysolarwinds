import logging
from pprint import pprint

import ipdb
from config import SNMPV2C, SW_ARGS

import solarwinds

format = "%(asctime)s %(levelname)s %(funcName)s %(lineno)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=format)

sw = solarwinds.api(**SW_ARGS)
"""
node_args = {
    "caption": "death-star",
    "ip_address": "172.16.1.1",
    "community": "3!3ph4n!",
    "rw_community": "1a6dr0v3r",
    "engine_id": 1,
    "custom_properties": {"Region": "AMER", "Site": "WTC - MIS - New York, NY"},
    "latitude": 40.713608,
    "longitude": -74.012143,
}
"""
node_args = {
    "caption": "RKHG55ER01",
    "ip_address": "172.25.53.10",
    "community": "3!3ph4n!",
    "rw_community": "1a6dr0v3r",
    "engine_id": 4,
    "custom_properties": {"Region": "APAC", "Site": "KHG - MA - Hong Kong, HK"},
    "latitude": 22.284868,
    "longitude": 114.154778,
}
node = sw.orion.node(**node_args)
# node = sw.orion.node(caption='RBFT08IN01', community='3!3ph4n!')
# node = sw.orion.node(caption="RBFT08IN01")
# node = sw.orion.node(ip_address="172.25.84.11")
# node = sw.orion.node(caption="RBCA04CR01")
# query = f"SELECT N.NodeID, N.Caption AS NodeName, I.InterfaceID, I.UnManaged, I.Caption AS InterfaceName FROM Orion.Nodes N JOIN Orion.NPM.Interfaces I ON N.NodeID = I.NodeID WHERE N.NodeID = {node.id}"
# existing_interfaces = node.api.query(query)
# all_interfaces = node.api.invoke(
#     "Orion.NPM.Interfaces", "DiscoverInterfacesOnNode", node.id
# )
ipdb.set_trace()
