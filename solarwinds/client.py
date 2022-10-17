import json
from datetime import datetime

import httpx
from solarwinds.utils import parse_response


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial


class SwisClient:
    def __init__(self, hostname, username, password, verify=True, timeout=60):
        self.url = f"https://{hostname}:17778/SolarWinds/InformationService/v3/Json/"
        self.client = httpx.Client(
            auth=(username, password),
            timeout=httpx.Timeout(timeout),
            headers={b"Content-Type": b"application/json"},
            limits=httpx.Limits(max_keepalive_connections=None, max_connections=None),
            verify=verify,
        )

    def query(self, query, **params):
        return parse_response(
            self._req("POST", "Query", {"query": query, "parameters": params}).json()
        )

    def invoke(self, entity, verb, *args):
        return self._req("POST", "Invoke/{}/{}".format(entity, verb), args).json()

    def create(self, entity, **properties):
        return self._req("POST", "Create/" + entity, properties).json()

    def read(self, uri):
        return self._req("GET", uri).json()

    def update(self, uri, **properties):
        self._req("POST", uri, properties)

    def bulkupdate(self, uris, **properties):
        self._req("POST", "BulkUpdate", {"uris": uris, "properties": properties})

    def delete(self, uri):
        self._req("DELETE", uri)

    def bulkdelete(self, uris):
        self._req("POST", "BulkDelete", {"uris": uris})

    def sql(self, statement: str) -> bool:
        """
        Workaround API to execute arbitrary SQL against Solarwinds DB
        **NOTE**: This method takes raw TSQL syntax, *NOT* SWQL syntax
        """
        return self.invoke("Orion.Reporting", "ExecuteSQL", statement)

    def _req(self, method, frag, data=None):
        resp = self.client.request(
            method, self.url + frag, data=json.dumps(data, default=_json_serial)
        )

        # try to extract reason from response when request returns error
        if 400 <= resp.status_code < 600:
            try:
                resp.reason = json.loads(resp.text)["Message"]
            except:
                pass

        resp.raise_for_status()
        return resp
