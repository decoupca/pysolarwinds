from typing import Optional

from pysolarwinds.endpoints.orion.credentials import OrionCredential
from pysolarwinds.swis import SWISClient


class OrionUserPassCredential(OrionCredential):
    def __init__(
        self,
        swis: SWISClient,
        id: Optional[int] = None,
        name: str = "",
        owner: str = "Orion",
        username: str = "",
        password: str = "",
    ) -> None:
        self.swis = swis
        self.id = id
        self.name = name
        self.owner = owner
        self.username = username
        self.password = password
        super().__init__()

    def _validate(self) -> None:
        if not self.name:
            raise ValueError("Must provide credential name.")
        if not self.username:
            raise ValueError("Must provide username.")
        if not self.password:
            raise ValueError("Must provide password.")

    def create(self) -> bool:
        self._validate()
        self.id = self.swis.invoke(
            self.endpoint,
            "CreateUsernamePasswordCredentials",
            self.name,
            self.username,
            self.password,
            self.owner,
        )
        return True

    def save(self) -> bool:
        if not self.exists():
            return self.create()
        else:
            self._validate()
            self.swis.invoke(
                self.endpoint,
                "UpdateUsernamePasswordCredentials",
                self.id,
                self.name,
                self.username,
                self.password,
            )

    def __repr__(self) -> str:
        return f"<OrionUserPassCredential: {self.name or self.id}>"
