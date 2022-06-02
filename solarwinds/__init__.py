import requests
from orionsdk import SwisClient
from solarwinds.models.orion import Orion


class api(object):
    def __init__(self, hostname, username, password, validate_certs=False):
        session = requests.Session()
        if validate_certs is False:
            requests.packages.urllib3.disable_warnings()
            session.verify = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        self.hostname = hostname
        self.username = username
        self.password = password
        self.swis = SwisClient(
            hostname=hostname, username=username, password=password, session=session
        )
        self.orion = Orion(self.swis)

    def query(self, query):
        result = self.swis.query(query)
        if result:
            return result["results"]


__all__ = [api]
