import datetime
import json
from typing import Optional, Union

import httpx
from httpx._types import VerifyTypes

from pysolarwinds.exceptions import SWISError
from pysolarwinds.utils import parse_response


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    return None


class SWISClient:
    """HTTP client wrapper for sending API requests to SWIS."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        verify: VerifyTypes = True,
        timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.verify = verify
        self.timeout = timeout
        self.client = httpx.Client(
            auth=(self.username, self.password),
            timeout=httpx.Timeout(self.timeout),
            headers={b"Content-Type": b"application/json"},
            limits=httpx.Limits(max_keepalive_connections=None, max_connections=None),
            verify=self.verify,
        )

    @property
    def url(self) -> str:
        return f"https://{self.host}:17778/SolarWinds/InformationService/v3/Json/"

    def query(self, query: str, **params) -> list:
        return parse_response(
            self._req("POST", "Query", {"query": query, "parameters": params}).json(),
        )

    def invoke(self, entity: str, verb: str, *args) -> dict:
        return self._req("POST", f"Invoke/{entity}/{verb}", args).json()

    def create(self, entity: str, **properties) -> dict:
        return self._req("POST", f"Create/{entity}", properties).json()

    def read(self, uri: str) -> dict:
        return self._req("GET", uri).json()

    def update(self, uris: Union[list[str], str], **properties):
        if isinstance(uris, list):
            self._req("POST", "BulkUpdate", {"uris": uris, "properties": properties})
        else:
            self._req("POST", uris, properties)

    def delete(self, uris: Union[list[str], str]):
        if isinstance(uris, list):
            self._req("POST", "BulkDelete", {"uris": uris})
        else:
            self._req("DELETE", uris)

    def sql(self, statement: str) -> bool:
        """Workaround API to execute arbitrary SQL against pysolarwinds DB
        **NOTE**: This method takes raw TSQL syntax, *NOT* SWQL syntax.
        Returns empty data structure if successful.
        """
        self.invoke("Orion.Reporting", "ExecuteSQL", statement)
        return True

    def _req(
        self, method: str, frag: str, data: Optional[dict] = None,
    ) -> httpx.Response:
        response = self.client.request(
            method, self.url + frag, data=json.dumps(data, default=_json_serial),
        )

        if 400 <= response.status_code < 600:
            error_msg = response.json().get("FullException")
            msg = f"{method} to {self.url + frag} returned {response.status_code}\n"
            if error_msg:
                msg = msg + "Full exception returned by SWIS:\n" + error_msg
            raise SWISError(msg)
        return response

    def __repr__(self) -> str:
        return (
            f"SWISClient(host={self.host}, username={self.username}, "
            f"password=********, verify={self.verify}, timeout={self.timeout})"
        )
