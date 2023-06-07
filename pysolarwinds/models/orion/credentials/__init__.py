from typing import Optional, Union

from pysolarwinds.entities.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.entities.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.entities.orion.credentials.userpass import UserPassCredential
from pysolarwinds.exceptions import SWError, SWNonUniqueResultError, SWObjectNotFound
from pysolarwinds.models import BaseModel
from pysolarwinds.models.orion.credentials.snmpv2 import SNMPv2CredentialsModel
from pysolarwinds.models.orion.credentials.snmpv3 import SNMPv3CredentialsModel
from pysolarwinds.models.orion.credentials.userpass import UserPassCredentialsModel


class CredentialsModel(BaseModel):
    name = "Credential"

    def __init__(self, swis):
        self.swis = swis
        self.snmpv2 = SNMPv2CredentialsModel(swis=swis)
        self.snmpv3 = SNMPv3CredentialsModel(swis=swis)
        self.userpass = UserPassCredentialsModel(swis=swis)

    def get(
        self, id: Optional[int] = None, name: Optional[str] = None
    ) -> Union[SNMPv2Credential, SNMPv3Credential, UserPassCredential]:
        if not id and not name:
            raise ValueError("Must provide either credential ID or name.")
        if id:
            return SNMPv3Credential(swis=self.swis, id=id)
        if name:
            query = (
                f"SELECT ID, Name, Description, CredentialType, CredentialOwner, Uri "
                f"FROM Orion.Credential WHERE Name='{name}'"
            )
            if result := self.swis.query(query):
                if len(result) > 1:
                    raise SWNonUniqueResultError(
                        f'More than one credential found with name "{name}".'
                    )
                cred_type = result[0]["CredentialType"]
                if cred_type.endswith("SnmpCredentialsV3"):
                    return SNMPv3Credential(swis=self.swis, data=result[0])
                elif cred_type.endswith("SnmpCredentialsV2"):
                    return SNMPv2Credential(swis=self.swis, data=result[0])
                elif cred_type.endswith("UsernamePasswordCredential"):
                    return UserPassCredential(swis=self.swis, data=result[0])
                else:
                    raise SWError(f"Unknown credential type: {cred_type}")
            else:
                raise SWObjectNotFound(f'Credential with name "{name}" not found.')
