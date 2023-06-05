from typing import Optional

from pysolarwinds.endpoints.orion.credentials.userpass import OrionUserPassCredential
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.models import BaseModel


class UserPassCredential(BaseModel):
    def get(
        self, name: Optional[str], id: Optional[int] = None
    ) -> OrionUserPassCredential:
        if not id and not name:
            raise ValueError("Must provide either credential ID or name.")
        if id:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE CredentialType='SolarWinds.Orion.Core.SharedCredentials.Credentials.UsernamePasswordCredential' "
                f"AND ID={id}"
            )
            if result := self.swis.query(query):
                return OrionUserPassCredential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(
                    f"Username/password credential with ID {id} not found."
                )
        elif name:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE CredentialType='SolarWinds.Orion.Core.SharedCredentials.Credentials.UsernamePasswordCredential' "
                f"AND Name='{name}'"
            )
            if result := self.swis.query(query):
                return OrionUserPassCredential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(
                    f'Username/password credential with name "{name}" not found.'
                )

    def create(
        self,
        name: str,
        username: str,
        password: str,
        owner: str = "Orion",
    ) -> OrionUserPassCredential:
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateUsernamePasswordCredentials",
            name,
            username,
            password,
            owner,
        )
        return OrionUserPassCredential(swis=self.swis, id=id)
