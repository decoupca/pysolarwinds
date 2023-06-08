"""SNMPv2 credentials model."""

from typing import Optional

import pypika

from pysolarwinds.entities.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.exceptions import SWObjectNotFoundError
from pysolarwinds.models import BaseModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE


class SNMPv2CredentialsModel(BaseModel):
    """SNMPv2 credentials model."""

    def get(
        self, name: Optional[str], id: Optional[int] = None
    ) -> Optional[SNMPv2Credential]:
        """Get a SNMPv2 credential.

        Args:
            name: Credential name.
            id: Credential ID.

        Returns:
            A `SNMPv2Credential` object if it exists, `None` otherwise.

        Raises:
            ValueError if neither `name` nor `id` is provided.
            SWObjectNotFoundError if no object was found.
        """
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
        """Create SNMPv2 credential.

        Args:
            name: Credential name (used only in SolarWinds).
            community: SNMPv2 community string.
            owner: Unknown significance.

        Returns:
            `SNMPv2Credential` object.

        Raises:
            None.
        """
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateSNMPCredentials",
            name,
            community,
            owner,
        )
        return SNMPv2Credential(swis=self.swis, id=id)
