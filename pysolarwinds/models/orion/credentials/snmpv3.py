from typing import Literal, Optional

import pypika

from pysolarwinds.endpoints.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.models import BaseModel


class SNMPv3CredentialsModel(BaseModel):
    def get(self, name: Optional[str], id: Optional[int] = None) -> SNMPv3Credential:
        if not id and not name:
            raise ValueError("Must provide either credential ID or name.")
        if id:
            criterion = pypika.Criterion.all(
                self.TABLE.CredentialType
                == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV3",
                self.TABLE.ID == id,
            )
            query = self.QUERY.where(criterion)
            if result := self.swis.query(query.get_sql()):
                return SNMPv3Credential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(f"SNMPv3 credential with ID {id} not found.")
        elif name:
            criterion = pypika.Criterion.all(
                self.TABLE.CredentialType
                == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV3",
                self.TABLE.Name == name,
            )
            query = self.QUERY.where(criterion)
            if result := self.swis.query(query.get_sql()):
                return SNMPv3Credential(swis=self.swis, data=result[0])
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
    ) -> SNMPv3Credential:
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
        return SNMPv3Credential(swis=self.swis, id=id)
