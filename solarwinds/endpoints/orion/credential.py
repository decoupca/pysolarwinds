from typing import Dict, Literal, Optional

from solarwinds.api import API
from solarwinds.endpoint import Endpoint
from solarwinds.exceptions import SWObjectExists, SWObjectPropertyError


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

    def __init__(self) -> None:
        if not self.id and not self.name:
            raise ValueError("must provide either credential ID or name")
        super().__init__()

    @property
    def type(self) -> Optional[str]:
        return self._swp.get("CredentialType")

    def _get_attr_updates(self) -> Dict:
        return {
            "id": self._swp.get("ID"),
            "name": self._swp.get("Name"),
        }

    def __repr__(self):
        return f"<OrionCredential: {self.name or self.id}>"

    def __str__(self) -> str:
        return self.name


class OrionSNMPv3Credential(OrionCredential):
    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: Optional[str] = None,
        owner: str = "Orion",
        description: Optional[str] = None,
        username: Optional[str] = None,
        context: Optional[str] = None,
        auth_method: Optional[Literal["md5", "sha1"]] = None,
        auth_password: Optional[str] = None,
        auth_key_is_password: Optional[bool] = None,
        priv_method: Optional[Literal["des56", "aes128", "aes192", "aes256"]] = None,
        priv_password: Optional[str] = None,
        priv_key_is_password: Optional[bool] = None,
    ) -> None:
        self.api = api
        self.id = id
        self.name = name
        self.owner = owner
        self.description = description
        self.username = username
        self.context = context
        self.auth_method = auth_method
        self.auth_password = auth_password
        self.auth_key_is_password = auth_key_is_password
        self.priv_method = priv_method
        self.priv_password = priv_password
        self.priv_key_is_password = priv_key_is_password
        super().__init__()

    def create(self) -> bool:
        raise NotImplementedError


class OrionSNMPv2Credential(OrionCredential):
    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: Optional[str] = None,
        community: Optional[str] = None,
        owner: str = "Orion",
    ) -> None:
        self.api = api
        self.id = id
        self.name = name
        self.community = community
        self.owner = owner
        super().__init__()

    def create(self) -> bool:
        if not self.name or not self.community:
            raise SWObjectPropertyError(f"Must provide name and community string")
        if self.exists():
            raise SWObjectExists(f"{self}: Credential already exists")
        else:
            self.id = self.api.invoke(
                self.endpoint,
                "CreateSNMPCredentials",
                self.name,
                self.community,
                self.owner,
            )
            return True


class OrionUserPassCredential(OrionCredential):
    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: Optional[str] = None,
        owner: str = "Orion",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.api = api
        self.id = id
        self.name = name
        self.owner = owner
        self.username = username
        self.password = password
        super().__init__()

    def create(self) -> bool:
        raise NotImplementedError
