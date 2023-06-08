from typing import Optional

import pypika

from pysolarwinds.entities.orion.credentials.userpass import UserPassCredential
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.models import BaseModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE


class UserPassCredentialsModel(BaseModel):
    def get(self, name: Optional[str], id: Optional[int] = None) -> UserPassCredential:
        if not id and not name:
            msg = "Must provide either credential ID or name."
            raise ValueError(msg)
        if id:
            criterion = pypika.Criterion.all(
                TABLE.CredentialType
                == "SolarWinds.Orion.Core.SharedCredentials.Credentials.UsernamePasswordCredential",
                id == TABLE.ID,
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return UserPassCredential(swis=self.swis, data=result[0])
            else:
                msg = f"Username/password credential with ID {id} not found."
                raise SWObjectNotFound(
                    msg,
                )
        elif name:
            criterion = pypika.Criterion.all(
                TABLE.CredentialType
                == "SolarWinds.Orion.Core.SharedCredentials.Credentials.UsernamePasswordCredential",
                TABLE.Name == name,
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return UserPassCredential(swis=self.swis, data=result[0])
            else:
                msg = f'Username/password credential with name "{name}" not found.'
                raise SWObjectNotFound(
                    msg,
                )
        return None

    def create(
        self,
        name: str,
        username: str,
        password: str,
        owner: str = "Orion",
    ) -> UserPassCredential:
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateUsernamePasswordCredentials",
            name,
            username,
            password,
            owner,
        )
        return UserPassCredential(swis=self.swis, id=id)
