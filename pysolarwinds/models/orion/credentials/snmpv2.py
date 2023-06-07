from typing import Optional

from pysolarwinds.endpoints.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.models import BaseModel


class SNMPv2Credential(BaseModel):
    def get(self, name: Optional[str], id: Optional[int] = None) -> SNMPv2Credential:
        if not id and not name:
            raise ValueError("Must provide either credential ID or name.")
        if id:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE CredentialType='SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV2' "
                f"AND ID={id}"
            )
            if result := self.swis.query(query):
                return SNMPv2Credential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(f"SNMPv2 credential with ID {id} not found.")
        elif name:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE CredentialType='SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV2' "
                f"AND Name='{name}'"
            )
            if result := self.swis.query(query):
                return SNMPv2Credential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(
                    f'SNMPv2 credential with name "{name}" not found.'
                )

    def create(
        self,
        name: str,
        community: str,
        owner: str = "Orion",
    ) -> SNMPv2Credential:
        id = self.swis.invoke(
            "Orion.Credential", "CreateSNMPCredentials", name, community, owner
        )
        return SNMPv2Credential(swis=self.swis, id=id)
