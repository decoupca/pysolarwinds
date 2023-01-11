from typing import Literal, Optional

from solarwinds.endpoints.orion.credential import (
    OrionSNMPv2Credential,
    OrionSNMPv3Credential,
    OrionUserPassCredential,
)
from solarwinds.model import BaseModel


class Credential(BaseModel):
    name = "Credential"

    def get(self, id: Optional[int] = None, name: Optional[str] = None):
        if id:
            query = f"SELECT ID, Name, Description, CredentialType, CredentialOwner FROM Orion.Credential WHERE ID = '{id}'"
        if name:
            query = f"SELECT ID, Name, Description, CredentialType, CredentialOwner FROM Orion.Credential WHERE Name = '{name}'"
        result = self.api.query(query)[0]

        if result:
            if result["CredentialType"].endswith("SnmpCredentialsV3"):
                return OrionSNMPv3Credential(
                    api=self.api,
                    id=id,
                    name=name,
                    owner=result["CredentialOwner"],
                    description=result["Description"],
                )
            if result["CredentialType"].endswith("SnmpCredentialsV2"):
                return OrionSNMPv2Credential(
                    api=self.api,
                    id=id,
                    name=name,
                    owner=result["CredentialOwner"],
                    description=result["Description"],
                )

    def snmpv2(
        self,
        id: Optional[int] = None,
        name: str = "",
        community: str = "",
        owner: str = "Orion",
    ) -> OrionSNMPv2Credential:
        return OrionSNMPv2Credential(
            api=self.api, id=id, name=name, community=community, owner=owner
        )

    def snmpv3(
        self,
        id: Optional[int] = None,
        name: str = "",
        description: str = "",
        owner: str = "Orion",
        username: str = "",
        context: str = "",
        auth_method: Optional[Literal["md5", "sha1", "sha256", "sha512"]] = None,
        auth_password: str = "",
        auth_key_is_password: bool = False,
        priv_method: Optional[Literal["des56", "aes128", "aes192", "aes256"]] = None,
        priv_password: str = "",
        priv_key_is_password: bool = False,
    ) -> OrionSNMPv3Credential:
        return OrionSNMPv3Credential(
            api=self.api,
            id=id,
            name=name,
            description=description,
            owner=owner,
            username=username,
            context=context,
            auth_method=auth_method,
            auth_password=auth_password,
            auth_key_is_password=auth_key_is_password,
            priv_method=priv_method,
            priv_password=priv_password,
            priv_key_is_password=priv_key_is_password,
        )

    def userpass(
        self,
        id: Optional[int] = None,
        name: str = "",
        username: str = "",
        password: str = "",
        owner: str = "Orion",
    ) -> OrionUserPassCredential:
        return OrionUserPassCredential(
            api=self.api,
            id=id,
            name=name,
            username=username,
            password=password,
            owner=owner,
        )
