from solarwinds.api import API
from solarwinds.models.orion import Orion


class api(object):
    def __init__(self, host, username, password, validate_cert=False):
        self.host = host
        self.username = username
        self.password = password
        self.api = API(
            host=host, username=username, password=password, validate_cert=validate_cert
        )
        self.swis = self.api.swis

        self.orion = Orion(self.swis)
