from typing import Dict, Optional

from solarwinds.api import API
from solarwinds.endpoint import Endpoint


class OrionCredential(Endpoint):
    endpoint = "Orion.Credential"
    _type = "credential"
    _id_attr = "credential_id"
    _attr_map = {
        "id": "ID",
        "name": "Name",
    }
    _swid_key = "ID"
    _swquery_attrs = ["id", "name"]
    _swargs_attrs = ["id", "name"]

    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        self.api = api
        self.id = id
        self.name = name
        self.description = description
        if not id and not name:
            raise ValueError("must provide either credential ID or name")
        super().__init__()

    def description(self) -> Optional[str]:
        return self._swp.get("Description")

    @property
    def owner(self) -> Optional[str]:
        return self._swp.get("CredentialOwner")

    @property
    def type(self) -> Optional[str]:
        return self._swp.get("CredentialType")

    def _get_attr_updates(self) -> Dict:
        swdata = self._swdata["properties"]
        return {
            "id": swdata.get("ID"),
            "name": swdata.get("Name"),
        }

    def __repr__(self):
        return f"<OrionCredential: {self.type}: {self.name or self.id}>"
