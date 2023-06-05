from typing import Literal, Optional

from pysolarwinds.endpoints.orion.credentials.snmpv3 import OrionSNMPv3Credential
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.models import BaseModel


class SNMPv3Credential(BaseModel):
    def get(
        self, name: Optional[str], id: Optional[int] = None
    ) -> OrionSNMPv3Credential:
        if not id and not name:
            raise ValueError("Must provide either credential ID or name.")
        if id:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE CredentialType='SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV3' "
                f"AND ID={id}"
            )
            if result := self.swis.query(query):
                return OrionSNMPv3Credential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(f"SNMPv3 credential with ID {id} not found.")
        elif name:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE CredentialType='SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV3' "
                f"AND Name='{name}'"
            )
            if result := self.swis.query(query):
                return OrionSNMPv3Credential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(
                    f'SNMPv3 credential with name "{name}" not found.'
                )

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
