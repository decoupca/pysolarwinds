from typing import Optional

from pysolarwinds.endpoints.orion.credentials.userpass import OrionUserPassCredential
from pysolarwinds.models import BaseModel


class UserPassCredential(BaseModel):
    def get(
        name: Optional[str] = None, id: Optional[int] = None
    ) -> OrionUserPassCredential:
        raise NotImplemented()

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
