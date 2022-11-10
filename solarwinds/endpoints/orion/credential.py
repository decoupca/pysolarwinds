from typing import Dict, Optional, Union

from solarwinds.api import API
from solarwinds.endpoint import Endpoint


class OrionCredential(Endpoint):
    endpoint = "Orion.Credential"
    _id_attr = "credential_id"
    _swid_key = "ID"
    _swquery_attrs = ["id", "name"]
    _swargs_attrs = ["id", "name"]

    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        credential_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        self.api = api
        self.id = id
        self.credential_type = credential_type
        self.name = name
        self.description = description
        if not id and not name:
            raise ValueError("must provide either credential ID or name")
        super().__init__()

    def _get_attr_updates(self) -> Dict:
        swdata = self._swdata["properties"]
        return {
            "credential_type": swdata.get("CredentialType"),
            "id": swdata.get("ID"),
            "name": swdata.get("Name"),
        }

    def __repr__(self):
        return f"<OrionCredential: {self.credential_type}: {self.name or self.id}>"
