from typing import Literal, Optional

from pysolarwinds.endpoints.orion.credentials import OrionCredential
from pysolarwinds.swis import SWISClient


class OrionSNMPv3Credential(OrionCredential):
    def save(self) -> bool:
        self.swis.invoke(
            "Orion.Credential",
            "UpdateSNMPv3Credentials",
            self.id,
            self.name,
            self.username,
            self.context,
            self.auth_method.upper() if self.auth_method else "None",
            self.auth_password,
            not self.auth_key_is_password,  # AFAICT, the SWIS API has this flag inverted
            self.priv_method.upper() if self.priv_method else "None",
            self.priv_password,
            not self.priv_key_is_password,  # AFAICT, the SWIS API has this flag inverted
        )
        return True

    def __repr__(self) -> str:
        return f"<OrionSNMPv3Credential: {self.name or self.id}>"
