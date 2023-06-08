"""Credentials model."""
from typing import Optional, Union

from pysolarwinds.entities.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.entities.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.entities.orion.credentials.userpass import UserPassCredential
from pysolarwinds.exceptions import (
    SWError,
    SWNonUniqueResultError,
    SWObjectNotFoundError,
)
from pysolarwinds.models import BaseModel
from pysolarwinds.models.orion.credentials.snmpv2 import SNMPv2CredentialsModel
from pysolarwinds.models.orion.credentials.snmpv3 import SNMPv3CredentialsModel
from pysolarwinds.models.orion.credentials.userpass import UserPassCredentialsModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE
from pysolarwinds.swis import SWISClient


class CredentialsModel(BaseModel):
    """Credentials model."""

    name = "Credential"

    def __init__(self, swis: SWISClient) -> None:
        self.swis = swis
        self.snmpv2 = SNMPv2CredentialsModel(swis=swis)
        self.snmpv3 = SNMPv3CredentialsModel(swis=swis)
        self.userpass = UserPassCredentialsModel(swis=swis)

    def get(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Union[SNMPv2Credential, SNMPv3Credential, UserPassCredential, None]:
        """Get a single credential.

        Args:
            id: Credential ID to retrieve.
            name: Credential name to retrieve.

        Returns:
            SNMPv2Credential, SNMPv3Credential, UserPassCredential, or None.

        Raises:
            ValueError if neither `id` nor `name` are provided.
            SWObjectNotFoundError if no credential matches name or ID.
        """
        if not id and not name:
            msg = "Must provide either credential ID or name."
            raise ValueError(msg)
        if id:
            return SNMPv3Credential(swis=self.swis, id=id)
        if name:
            query = QUERY.where(TABLE.Name == name)
            if result := self.swis.query(str(query)):
                if len(result) > 1:
                    msg = f'More than one credential found with name "{name}".'
                    raise SWNonUniqueResultError(
                        msg,
                    )
                cred_type = result[0]["CredentialType"]
                if cred_type.endswith("SnmpCredentialsV3"):
                    return SNMPv3Credential(swis=self.swis, data=result[0])
                elif cred_type.endswith("SnmpCredentialsV2"):
                    return SNMPv2Credential(swis=self.swis, data=result[0])
                elif cred_type.endswith("UsernamePasswordCredential"):
                    return UserPassCredential(swis=self.swis, data=result[0])
                else:
                    msg = f"Unknown credential type: {cred_type}"
                    raise SWError(msg)
            else:
                msg = f'Credential with name "{name}" not found.'
                raise SWObjectNotFoundError(msg)
        return None
