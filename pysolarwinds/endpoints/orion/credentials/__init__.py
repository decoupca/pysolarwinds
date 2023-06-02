from typing import Dict, Literal, Optional

from pysolarwinds.endpoints import NewEndpoint
from pysolarwinds.exceptions import SWObjectExists
from pysolarwinds.swis import SWISClient


class OrionCredential(NewEndpoint):
    _entity_type = "Orion.Credential"
    _uri_template = "swis://{}/Orion/Orion.Credential/ID={}"
    _write_attr_map = {
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

    @property
    def type(self) -> str:
        return self.data.get("CredentialType", "")

    def __repr__(self):
        if self.name:
            return f"OrionCredential(name='{self.name}')"
        else:
            return f"OrionCredential(id={self.id})>"

    def __str__(self) -> str:
        return self.name
