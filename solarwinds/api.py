import json
from datetime import datetime
from typing import Dict, List, Optional, Union
from solarwinds.exceptions import SWISError

import httpx

from solarwinds.utils import parse_response


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial


class API:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        verify: Union[bool, str] = True,
        timeout: int = 60,
    ):
        self.hostname = hostname
        self.client = httpx.Client(
            auth=(username, password),
            timeout=httpx.Timeout(timeout),
            headers={b"Content-Type": b"application/json"},
            limits=httpx.Limits(max_keepalive_connections=None, max_connections=None),
            verify=verify,
        )

    @property
    def url(self) -> str:
        return f"https://{self.hostname}:17778/SolarWinds/InformationService/v3/Json/"

    def query(self, query: str, **params) -> List:
        return parse_response(
            self._req("POST", "Query", {"query": query, "parameters": params}).json()
        )

    def invoke(self, entity: str, verb: str, *args) -> Dict:
        return self._req("POST", f"Invoke/{entity}/{verb}", args).json()

    def create(self, entity: str, **properties) -> Dict:
        return self._req("POST", f"Create/{entity}", properties).json()

    def read(self, uri: str) -> Dict:
        return self._req("GET", uri).json()

    def update(self, uris: Union[List[str], str], **properties):
        if isinstance(uris, list):
            self._req("POST", "BulkUpdate", {"uris": uris, "properties": properties})
        else:
            self._req("POST", uris, properties)

    def delete(self, uris: Union[List[str], str]):
        if isinstance(uris, list):
            self._req("POST", "BulkDelete", {"uris": uris})
        else:
            self._req("DELETE", uris)

    def sql(self, statement: str) -> bool:
        """
        Workaround API to execute arbitrary SQL against Solarwinds DB
        **NOTE**: This method takes raw TSQL syntax, *NOT* SWQL syntax
        Returns empty data structure if successful
        """
        self.invoke("Orion.Reporting", "ExecuteSQL", statement)
        return True

    def _req(self, method: str, frag: str, data: Optional[Dict] = None):
        response = self.client.request(
            method, self.url + frag, data=json.dumps(data, default=_json_serial)
        )

        if 400 <= response.status_code < 600:
            error_msg = response.json().get("FullException")
            msg = f"{method} to {self.url + frag} returned {response.status_code}\n"
            if error_msg:
                msg = msg + "Full exception returned by SWIS:\n" + error_msg
            raise SWISError(msg)
        return response
