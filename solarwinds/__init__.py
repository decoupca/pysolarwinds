import requests
from orionsdk import SwisClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from solarwinds.models.orion import Orion


class api(object):
    def __init__(self, host, username, password, validate_certs=False):
        if validate_certs is False:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.host = host
        self.username = username
        self.password = password
        self.swis = SwisClient(host, username, password)
        self.orion = Orion(self.swis)


__all__ = [api]
