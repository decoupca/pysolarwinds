from typing import Dict, Optional

from solarwinds.api import API
from solarwinds.endpoint import Endpoint


class OrionEngine(Endpoint):
    endpoint = "Orion.Engines"
    _type = "engine"
    _id_attr = "id"
    _swid_key = "EngineID"
    _attr_map = {
        "id": "EngineID",
        "name": "ServerName",
        "ip_address": "IP",
    }
    _swquery_attrs = ["id", "name", "ip_address"]
    _swargs_attrs = ["id", "name", "ip_address"]

    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        ip_address: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.api = api
        self.id = id
        self.ip_address = ip_address
        self.name = name
        super().__init__()

    def _get_attr_updates(self) -> Dict:
        swdata = self._swdata["properties"]
        return {
            "ip_address": swdata.get("IP"),
            "id": swdata.get("ID"),
            "name": swdata.get("ServerName"),
        }

    def __repr__(self):
        return f"<OrionEngine: {self.name or self.ip_address or self.id}>"
