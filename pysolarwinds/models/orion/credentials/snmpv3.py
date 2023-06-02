from typing import Literal, Optional

from pysolarwinds.endpoints.orion.credentials.snmpv3 import OrionSNMPv3Credential
from pysolarwinds.models import BaseModel


class SNMPv3Credential(BaseModel):
    def get(self) -> OrionSNMPv3Credential:
        pass

    def create(
        self,
        name: str,
        username: str,
        auth_method: Literal["md5", "sha1", "sha256", "sha512"],
        auth_password: str,
        priv_method: Literal["des56", "aes128", "aes192", "aes256"],
        priv_password: str,
        auth_key_is_password: bool = False,
        priv_key_is_password: bool = False,
        context: str = "",
        owner: str = "Orion",
    ) -> OrionSNMPv3Credential:
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateSNMPv3Credentials",
            name,
            username,
            context,
            auth_method.upper() if self.auth_method else "None",
            auth_password,
            not auth_key_is_password,  # AFAICT, the SWIS SWISClient has this flag inverted
            priv_method.upper() if self.priv_method else "None",
            priv_password,
            not priv_key_is_password,  # AFAICT, the SWIS SWISClient has this flag inverted
            owner,
        )
        return OrionSNMPv3Credential(swis=self.swis, id=id)
