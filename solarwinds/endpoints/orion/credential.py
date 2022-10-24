from typing import Union

from solarwinds.client import SwisClient
from solarwinds.endpoint import Endpoint


class OrionCredential(Endpoint):
    endpoint = "Orion.Credential"
    _id_attr = "credential_id"
    _swid_key = "ID"
    _swquery_attrs = ["id", "name"]
    _swargs_attrs = ["id", "name"]

    def __init__(
        self,
        swis: SwisClient,
        id: Union[int, None] = None,
        credential_type: Union[str, None] = None,
        name: Union[str, None] = None,
        description: Union[str, None] = None,
    ):
        self.swis = swis
        self.id = id
        self.credential_type = credential_type
        self.name = name
        self.description = description
        if id is None and name is None:
            raise ValueError("must provide either credential ID or name")
        super().__init__()

    def _get_attr_updates(self) -> dict:
        swdata = self._swdata["properties"]
        return {
            "credential_type": swdata.get("CredentialType"),
            "id": swdata.get("ID"),
            "name": swdata.get("Name"),
        }

    def __repr__(self):
        return f"<OrionCredential: {self.name or self.id}>"
