from typing import Optional

from pysolarwinds.entities.orion.credentials import Credential


class UserPassCredential(Credential):
    def update(
        self,
        username: str,
        password: str,
        name: Optional[str] = None,
    ) -> None:
        """
        Update username/password credential set.

        The way the SWIS API is built, it is not possible to update only one attribute;
        if you want to update any attribute, you must provide all.

        Arguments:
            username: The username to update.
            password: The password to update.
            name: The credential set name to update.

        """
        if name is None:
            name = self.name
        self.swis.invoke(
            "Orion.Credential",
            "UpdateUsernamePasswordCredentials",
            self.id,
            name,
            username,
            password,
        )

    def __repr__(self) -> str:
        return f"UserPassCredential(id={self.id})"
