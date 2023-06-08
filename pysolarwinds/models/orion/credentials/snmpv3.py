"""SNMPV3 credentials model."""
from typing import Literal, Optional

import pypika

from pysolarwinds.entities.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.exceptions import SWObjectNotFoundError
from pysolarwinds.models import BaseModel
from pysolarwinds.queries.orion.credentials import QUERY, TABLE


class SNMPv3CredentialsModel(BaseModel):
    """SNMPV3 credentials model."""

    def get(self, name: Optional[str], id: Optional[int] = None) -> SNMPv3Credential:
        """Get a SNMPv3 credential.

        Args:
            name: Name of credential to retrieve.
            id: ID of credential to retrieve.

        Returns:
            `SNMPv3Credential` object.

        Raises:
            ValueError if neither `name` nor `id` is provided.
        """
        if not id and not name:
            msg = "Must provide either credential ID or name."
            raise ValueError(msg)
        if id:
            criterion = pypika.Criterion.all(
                TABLE.CredentialType
                == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV3",
                id == TABLE.ID,
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return SNMPv3Credential(swis=self.swis, data=result[0])
            msg = f"SNMPv3 credential with ID {id} not found."
            raise SWObjectNotFoundError(msg)
        elif name:  # noqa: RET506
            criterion = pypika.Criterion.all(
                TABLE.CredentialType
                == "SolarWinds.Orion.Core.Models.Credentials.SnmpCredentialsV3",
                TABLE.Name == name,
            )
            query = QUERY.where(criterion)
            if result := self.swis.query(str(query)):
                return SNMPv3Credential(swis=self.swis, data=result[0])
            msg = f'SNMPv3 credential with name "{name}" not found.'
            raise SWObjectNotFoundError(
                msg,
            )
        return None

    def create(
        self,
        name: str,
        username: str,
        auth_method: Literal["md5", "sha1", "sha256", "sha512"],
        auth_password: str,
        priv_method: Literal["des56", "aes128", "aes192", "aes256"],
        priv_password: str,
        *,
        auth_key_is_password: bool,
        priv_key_is_password: bool,
        context: str = "",
        owner: str = "Orion",
    ) -> SNMPv3Credential:
        """Create new SNMPv3 credential.

        Args:
            name: Credential name (used in SolarWinds only).
            username: SNMPv3 username.
            auth_method: Protocol to use for authentication.
            auth_password: Authentication secret.
            priv_method: Protocol to use for privacy.
            priv_password: Privacy secret.
            auth_key_is_password: Unknown significance.
            priv_key_is_password: Unknown significance.
            context: (Optional) SNMPv3 context.
            owner: SolarWinds owner. Unknown significance.

        Returns:
            `SNMPv3Credential` object.

        Raises:
            None.
        """
        id = self.swis.invoke(
            "Orion.Credential",
            "CreateSNMPv3Credentials",
            name,
            username,
            context,
            auth_method.upper() if auth_method else "None",
            auth_password,
            not auth_key_is_password,  # AFAICT, the SWIS SWISClient has this flag inverted
            priv_method.upper() if priv_method else "None",
            priv_password,
            not priv_key_is_password,  # AFAICT, the SWIS SWISClient has this flag inverted
            owner,
        )
        return SNMPv3Credential(swis=self.swis, id=id)
