from typing import Literal, Optional

from solarwinds.endpoints.orion.credential import (
    OrionSNMPv2Credential,
    OrionSNMPv3Credential,
    OrionUserPassCredential,
)
from solarwinds.model import BaseModel


class Credential(BaseModel):
    name = "Credential"

    def snmpv2(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        community: Optional[str] = None,
        owner: str = "Orion",
    ) -> OrionSNMPv2Credential:
        return OrionSNMPv2Credential(
            api=self.api, id=id, name=name, community=community, owner=owner
        )

    def snmpv3(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        owner: str = "Orion",
        username: Optional[str] = None,
        context: Optional[str] = None,
        auth_method: Optional[Literal["md5", "sha1"]] = None,
        auth_password: Optional[str] = None,
        auth_key_is_password: Optional[bool] = None,
        priv_method: Optional[Literal["des56", "aes128", "aes192", "aes256"]] = None,
        priv_password: Optional[str] = None,
        priv_key_is_password: Optional[bool] = None,
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
        name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
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
