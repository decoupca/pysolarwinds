from typing import Dict, Literal, Optional

from pysolarwinds.api import API
from pysolarwinds.endpoint import Endpoint
from pysolarwinds.exceptions import SWObjectExists


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
    VALID_AUTH_METHODS = [None, "md5", "sha1", "sha256", "sha512"]
    VALID_PRIV_METHODS = [None, "des56", "aes128", "aes192", "aes256"]

    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: str = "",
        owner: str = "Orion",
        description: str = "",
        username: str = "",
        context: str = "",
        auth_method: Optional[Literal["md5", "sha1", "sha256", "sha512"]] = None,
        auth_password: str = "",
        auth_key_is_password: bool = False,
        priv_method: Optional[Literal["des56", "aes128", "aes192", "aes256"]] = None,
        priv_password: str = "",
        priv_key_is_password: bool = False,
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

    def _validate(self) -> None:
        if not self.name:
            raise ValueError("Must provide credential name.")
        if not self.username:
            raise ValueError("Must provide username.")
        if self.auth_method not in self.VALID_AUTH_METHODS:
            raise ValueError(f"auth_method must be: {self.VALID_AUTH_METHODS}")
        if self.priv_method not in self.VALID_PRIV_METHODS:
            raise ValueError(f"priv_method must be: {self.VALID_PRIV_METHODS}")

    def create(self) -> bool:
        if self.exists():
            raise SWObjectExists
        self._validate()
        self.id = self.api.invoke(
            self.endpoint,
            "CreateSNMPv3Credentials",
            self.name,
            self.username,
            self.context,
            self.auth_method.upper() if self.auth_method else "None",
            self.auth_password,
            not self.auth_key_is_password,  # AFAICT, the SWIS API has this flag inverted
            self.priv_method.upper() if self.priv_method else "None",
            self.priv_password,
            not self.priv_key_is_password,  # AFAICT, the SWIS API has this flag inverted
            self.owner,
        )
        return True

    def save(self) -> bool:
        if not self.exists():
            return self.create()
        else:
            self._validate()
            self.api.invoke(
                self.endpoint,
                "UpdateSNMPv3Credentials",
                self.id,
                self.name,
                self.username,
                self.context,
                self.auth_method.upper() if self.auth_method else "None",
                self.auth_password,
                not self.auth_key_is_password,  # AFAICT, the SWIS API has this flag inverted
                self.priv_method.upper() if self.priv_method else "None",
                self.priv_password,
                not self.priv_key_is_password,  # AFAICT, the SWIS API has this flag inverted
            )
            return True

    def __repr__(self) -> str:
        return f"<OrionSNMPv3Credential: {self.name or self.id}>"


class OrionSNMPv2Credential(OrionCredential):
    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: str = "",
        community: str = "",
        owner: str = "Orion",
    ) -> None:
        self.api = api
        self.id = id
        self.name = name
        self.community = community
        self.owner = owner
        super().__init__()

    def _validate(self) -> None:
        if not self.name:
            raise ValueError("Must provide credential name.")
        if not self.community:
            raise ValueError("Must provide community string.")

    def create(self) -> bool:
        if self.exists():
            raise SWObjectExists()
        self._validate()

        self.id = self.api.invoke(
            self.endpoint,
            "CreateSNMPCredentials",
            self.name,
            self.community,
            self.owner,
        )
        return True

    def save(self) -> bool:
        if not self.exists():
            return self.create()
        else:
            self._validate()
            self.api.invoke(
                self.endpoint,
                "UpdateSNMPCredentials",
                self.id,
                self.name,
                self.community,
            )
            return True

    def __repr__(self) -> str:
        return f"<OrionSNMPv2Credential: {self.name or self.id}>"


class OrionUserPassCredential(OrionCredential):
    def __init__(
        self,
        api: API,
        id: Optional[int] = None,
        name: str = "",
        owner: str = "Orion",
        username: str = "",
        password: str = "",
    ) -> None:
        self.api = api
        self.id = id
        self.name = name
        self.owner = owner
        self.username = username
        self.password = password
        super().__init__()

    def _validate(self) -> None:
        if not self.name:
            raise ValueError("Must provide credential name.")
        if not self.username:
            raise ValueError("Must provide username.")
        if not self.password:
            raise ValueError("Must provide password.")

    def create(self) -> bool:
        if self.exists():
            raise SWObjectExists
        else:
            self._validate()
            self.id = self.api.invoke(
                self.endpoint,
                "CreateUsernamePasswordCredentials",
                self.name,
                self.username,
                self.password,
                self.owner,
            )
            return True

    def save(self) -> bool:
        if not self.exists():
            return self.create()
        else:
            self._validate()
            self.api.invoke(
                self.endpoint,
                "UpdateUsernamePasswordCredentials",
                self.id,
                self.name,
                self.username,
                self.password,
            )

    def __repr__(self) -> str:
        return f"<OrionUserPassCredential: {self.name or self.id}>"
