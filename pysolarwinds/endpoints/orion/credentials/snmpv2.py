from typing import Optional

from pysolarwinds.endpoints.orion.credentials import OrionCredential
from pysolarwinds.swis import SWISClient


class OrionSNMPv2Credential(OrionCredential):
    def _validate(self) -> None:
        if not self.name:
            raise ValueError("Must provide credential name.")
        if not self.community:
            raise ValueError("Must provide community string.")

    def save(self) -> bool:
        self._validate()
        self.swis.invoke(
            self._entity_type,
            "UpdateSNMPCredentials",
            self.id,
            self.name,
            self.community,
        )
        return True

    def __repr__(self) -> str:
        return f"<OrionSNMPv2Credential: {self.name or self.id}>"
