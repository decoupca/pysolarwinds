from typing import Optional

import pypika

from pysolarwinds.entities.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.exceptions import SWObjectNotFound
from pysolarwinds.models import BaseModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE


class SNMPv2CredentialsModel(BaseModel):
    def get(self, name: Optional[str], id: Optional[int] = None) -> SNMPv2Credential:
        if not id and not name:
            raise ValueError("Must provide either credential ID or name.")
        if id:
            criterion = pypika.Criterion.all(
                TABLE.CredentialType
                == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV2",
                TABLE.ID == id,
            )
            query = self.QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return SNMPv2Credential(swis=self.swis, data=result[0])
            else:
                raise SWObjectNotFound(f"SNMPv2 credential with ID {id} not found.")
        elif name:
            criterion = pypika.Criterion.all(
                TABLE.CredentialType
                == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV2",
                TABLE.Name == name,
            )
            query = self.QUERY.where(criterion)
            if result := self.swis.query(str(query)):
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
