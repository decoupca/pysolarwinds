import requests
from orionsdk import SwisClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pysolarwinds.models.node import Node


class Solarwinds(object):
    def __init__(self, host, username, password, snmpv2c=None, validate_cert=False):
        if not validate_cert:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.host = host
        self.username = username
        self.password = password
        self.snmpv2c = snmpv2c
        self.swis = SwisClient(host, username, password)

    def node(self, **kwargs):
        return Node(self.swis, snmpv2c=self.snmpv2c, **kwargs)
