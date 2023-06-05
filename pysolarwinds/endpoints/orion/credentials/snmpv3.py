from typing import Literal, Optional

from pysolarwinds.endpoints.orion.credentials import OrionCredential
from pysolarwinds.swis import SWISClient


class OrionSNMPv3Credential(OrionCredential):
    def update(
        self,
        username: str,
        auth_method: Literal["md5", "sha1", "sha256", "sha512"],
        auth_password: str,
        auth_key_is_password: bool,
        priv_method: Literal["des56", "aes128", "aes192", "aes256"],
        priv_password: str,
        priv_key_is_password: bool,
        name: Optional[str] = None,
        context: str = "",
    ) -> None:
        """
        Update credential set with provided details.

        Due to how the SWIS API is built, there is no way to update only one property of the
        credential set; if you need to update any property, you must provide all properties.
        """
        if name is None:
            name = self.name
        self.swis.invoke(
            "Orion.Credential",
            "UpdateSNMPv3Credentials",
            self.id,
            name,
            username,
            context,
            auth_method.upper() if auth_method else "None",
            auth_password,
            not auth_key_is_password,  # AFAICT, the SWIS API has this flag inverted
            priv_method.upper() if priv_method else "None",
            priv_password,
            not priv_key_is_password,  # AFAICT, the SWIS API has this flag inverted
        )

    def __repr__(self) -> str:
        return f"OrionSNMPv3Credential(name='{self.name}')"
