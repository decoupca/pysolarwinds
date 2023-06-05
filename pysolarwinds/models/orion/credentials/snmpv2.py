from typing import Optional

from pysolarwinds.endpoints.orion.credentials.snmpv2 import OrionSNMPv2Credential
from pysolarwinds.models import BaseModel


class SNMPv2Credential(BaseModel):
    def get(self) -> OrionSNMPv2Credential:
        raise NotImplemented()

    def create(
        self,
        name: str,
        community: str,
        owner: str = "Orion",
    ) -> OrionSNMPv2Credential:
        id = self.swis.invoke(
            "Orion.Credential", "CreateSNMPCredentials", name, community, owner
        )
        return OrionSNMPv2Credential(swis=self.swis, id=id)
