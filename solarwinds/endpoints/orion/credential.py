from solarwinds.client import SwisClient
from solarwinds.endpoint import Endpoint


class OrionCredential(Endpoint):
    endpoint = "Orion.Credential"
    _id_attr = "credential_id"
    _swid_key = "ID"
    _swquery_attrs = ["id", "name"]

    def __init__(
        self,
        swis: SwisClient,
        id: int = None,
        name: str = None,
        description: str = None,
    ):
        self.swis = swis
        self.id = id
        self.name = name
        self.description = description
        if id is None and name is None:
            raise ValueError("must provide either credential ID or name")
        super().__init__()
