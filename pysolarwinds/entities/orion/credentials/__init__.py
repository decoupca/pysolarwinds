from typing import Optional

from pysolarwinds.entities import Entity
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.swis import SWISClient


class Credential(Entity):
    TYPE = "Orion.Credential"
    URI_TEMPLATE = "swis://{}/Orion/Orion.Credential/ID={}"
    WRITE_ATTR_MAP = {
        "name": "Name",
    }

    def __init__(
        self,
        swis: SWISClient,
        id: Optional[int] = None,
        uri: Optional[str] = None,
        data: Optional[dict] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(swis=swis, data=data, uri=uri, id=id, name=name)
        self.name = name or self.data.get("Name", "")

    def _get_uri(self) -> Optional[str]:
        if self.name:
            query = f"SELECT Uri FROM Orion.Credential WHERE Name='{self.name}'"
            if result := self.swis.query(query):
                return result[0]["Uri"]
            else:
                msg = f'No credential with name "{self.poller_type}" found.'
                raise SWObjectNotFound(
                    msg,
                )
        return None

    @property
    def _id(self) -> int:
        return self.data["ID"]

    @property
    def owner(self) -> str:
        return self.data["Owner"]

    @property
    def type(self) -> str:
        return self.data.get("CredentialType", "")

    def __repr__(self) -> str:
        return f"Credential(name='{self.name}')"

    def __str__(self) -> str:
        return self.name
