"""User/password credentials model."""
from typing import Optional

import pypika

from pysolarwinds.entities.orion.credentials.userpass import UserPassCredential
from pysolarwinds.exceptions import SWObjectNotFoundError
from pysolarwinds.models import BaseModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE


class UserPassCredentialsModel(BaseModel):
    """User/password credentials model."""

    def get(
        self, name: Optional[str], id: Optional[int] = None
    ) -> Optional[UserPassCredential]:
        """Get a user/password credential.

        Args:
            name: Credential name.
            id: Credential ID.

        Returns:
            `UserPassCredential` object.

        Raises:
            ValueError if neither `name` nor `id` is provided.
        """
        if not id and not name:
            msg = "Must provide either credential ID or name."
            raise ValueError(msg)
        if id:
            criterion = pypika.Criterion.all(
                [
                    TABLE.CredentialType
                    == "SolarWinds.Orion.Core.SharedCredentials.Credentials.UsernamePasswordCredential",
                    id == TABLE.ID,
                ]
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return UserPassCredential(swis=self.swis, data=result[0])
            msg = f"Username/password credential with ID {id} not found."
            raise SWObjectNotFoundError(
                msg,
            )
        elif name:  # noqa RET506
            criterion = pypika.Criterion.all(
                [
                    TABLE.CredentialType
                    == "SolarWinds.Orion.Core.SharedCredentials.Credentials.UsernamePasswordCredential",
                    TABLE.Name == name,
                ]
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return UserPassCredential(swis=self.swis, data=result[0])
            msg = f'Username/password credential with name "{name}" not found.'
            raise SWObjectNotFoundError(
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
        """Create a user/password credential.

        Args:
            name: Credential name.
            username: Credential username.
            password: Credential password.
            owner: Credential owner. Unknown significance.

        Returns:
            `UserPassCredential` object.

        Raises:
            None.
        """
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateUsernamePasswordCredentials",
            name,
            username,
            password,
            owner,
        )
        return UserPassCredential(swis=self.swis, id=id)
