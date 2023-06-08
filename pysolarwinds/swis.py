"""SolarWinds Information Service Client."""

import datetime
import json
import ssl
from typing import Any, Optional, Union

import httpx

from pysolarwinds.exceptions import SWISError
from pysolarwinds.utils import parse_response


def _json_serial(obj: Any) -> Optional[str]:
    """Serializer for objects not serializable by JSON."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return None


class SWISClient:
    """HTTP client wrapper for sending API calls to SWIS."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        verify: Union[str, bool, ssl.SSLContext],
        timeout: float = 30.0,
    ) -> None:
        """Initialize SWISClient.

        Args:
            host: FQDN or IP address of SolarWinds server.
            username: Username for authentication.
            password: Password fof authentication.
            verify: Options for verifying SSL certificate. See httpx documentation
                for details.
            timeout: Default timeout for all HTTP operations.


        Returns:
            None.

        Raises:
            None.
        """
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
        """SWIS API URL."""
        return f"https://{self.host}:17778/SolarWinds/InformationService/v3/Json/"

    def query(self, query: str, **params: dict) -> list[dict]:
        """Query SWIS for arbitrary information.

        Args:
            query: The SWQL query to execute.
            params: Additional params to pass along with the query.

        Returns:
            A list of result dictionaries.

        Raises:
            None.
        """
        return parse_response(
            self._req("POST", "Query", {"query": query, "parameters": params}).json(),
        )

    def invoke(self, entity: str, verb: str, *args: Any) -> Union[dict, int]:
        """Invoke a SWIS verb on an entity.

        Args:
            entity: The entity type to invoke `verb` on.
            verb: The verb to invoke. Refer to the SWIS schema documentation
                for available verbs.
            args: One or more arguments to pass to the verb.

        Returns:
            A dictionary with info on the response of the verb.

        Raises:
            None.
        """
        return self._req(
            method="POST", frag=f"Invoke/{entity}/{verb}", data=args
        ).json()

    def create(self, entity: str, **properties: Any) -> dict:
        """Create a new entity.

        Args:
            entity: The entity type to create. Corresponds to the SWIS table
                (e.g. Orion.Nodes for nodes).
            properties: A dictionary of properties to create the entity with.

        Returns:
            A dictionary of data about the created entity.

        Raises:
            None.
        """
        return self._req("POST", frag=f"Create/{entity}", data=properties).json()

    def read(self, uri: str) -> dict:
        """Read all data (properties) about an entity.

        Args:
            uri: A single SWIS URI to read data about.

        Returns:
            A dictionary of all properties.

        Raises:
            None.
        """
        return self._req("GET", uri).json()

    def update(self, uris: Union[list[str], str], **properties: Any) -> None:
        """Update one or more entities.

        Args:
            uris: One or more SWIS URIs to update.
            properties: Dictionary of properties to update on all entities.

        Returns:
            None.

        Raises:
            None.

        """
        if isinstance(uris, list):
            self._req("POST", "BulkUpdate", {"uris": uris, "properties": properties})
        else:
            self._req("POST", uris, properties)

    def delete(self, uris: Union[list[str], str]) -> None:
        """Delete one or more entities.

        Args:
            uris: One or more SWIS URIs to delete.

        Returns:
            None.

        Raises:
            None.

        """
        if isinstance(uris, list):
            self._req("POST", "BulkDelete", {"uris": uris})
        else:
            self._req("DELETE", uris)

    def sql(self, statement: str) -> None:
        """Workaround API to execute arbitrary SQL against SolarWinds DB.

        **NOTE**: This method takes raw TSQL syntax, *NOT* SWQL syntax.
        Returns empty data structure if successful.

        Args:
            statement: Raw TSQL statement.

        Returns:
            None.

        Raises:
            None.
        """
        self.invoke("Orion.Reporting", "ExecuteSQL", statement)

    def _req(
        self,
        method: str,
        frag: str,
        data: Any = None,
    ) -> httpx.Response:
        response = self.client.request(
            method,
            self.url + frag,
            data=json.dumps(data, default=_json_serial),
        )

        if 400 <= response.status_code < 600:  # noqa: PLR2004
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
