from typing import Optional

import pypika

from pysolarwinds.entities.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.exceptions import SWObjectNotFoundError
from pysolarwinds.models import BaseModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE


class SNMPv2CredentialsModel(BaseModel):
    def get(
        self, name: Optional[str], id: Optional[int] = None
    ) -> Optional[SNMPv2Credential]:
        if not id and not name:
            msg = "Must provide either credential ID or name."
            raise ValueError(msg)
        if id:
            criterion = pypika.Criterion.all(
                [
                    TABLE.CredentialType
                    == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV2",
                    id == TABLE.ID,
                ],
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return SNMPv2Credential(swis=self.swis, data=result[0])
            msg = f"SNMPv2 credential with ID {id} not found."
            raise SWObjectNotFoundError(msg)
        elif name:  # noqa
            criterion = pypika.Criterion.all(
                [
                    TABLE.CredentialType
                    == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV2",
                    TABLE.Name == name,
                ],
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return SNMPv2Credential(swis=self.swis, data=result[0])
            msg = f'SNMPv2 credential with name "{name}" not found.'
            raise SWObjectNotFoundError(
                msg,
            )
        return None

    def create(
        self,
        name: str,
        community: str,
        owner: str = "Orion",
    ) -> SNMPv2Credential:
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateSNMPCredentials",
            name,
            community,
            owner,
        )
        return SNMPv2Credential(swis=self.swis, id=id)
