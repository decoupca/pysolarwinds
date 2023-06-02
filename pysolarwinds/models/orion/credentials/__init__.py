from typing import Literal, Optional

from pysolarwinds.endpoints.orion.credentials.snmpv2 import OrionSNMPv2Credential
from pysolarwinds.endpoints.orion.credentials.snmpv3 import OrionSNMPv3Credential
from pysolarwinds.models import BaseModel
from pysolarwinds.models.orion.credentials.snmpv2 import SNMPv2Credential
from pysolarwinds.models.orion.credentials.snmpv3 import SNMPv3Credential
from pysolarwinds.models.orion.credentials.userpass import UserPassCredential


class Credentials(BaseModel):
    name = "Credential"

    def __init__(self, swis):
        self.swis = swis
        self.snmpv2 = SNMPv2Credential(swis=swis)
        self.snmpv3 = SNMPv3Credential(swis=swis)
        self.userpass = UserPassCredential(swis=swis)

    def get(self, id: Optional[int] = None, name: Optional[str] = None):
        if id:
            query = f"SELECT ID, Name, Description, CredentialType, CredentialOwner FROM Orion.Credential WHERE ID = '{id}'"
        if name:
            query = f"SELECT ID, Name, Description, CredentialType, CredentialOwner FROM Orion.Credential WHERE Name = '{name}'"
        result = self.swis.query(query)[0]

        if result:
            if result["CredentialType"].endswith("SnmpCredentialsV3"):
                return OrionSNMPv3Credential(
                    swis=self.swis,
                    id=id,
                    name=name,
                    owner=result["CredentialOwner"],
                    description=result["Description"],
                )
            if result["CredentialType"].endswith("SnmpCredentialsV2"):
                return OrionSNMPv2Credential(
                    swis=self.swis,
                    id=id,
                    name=name,
                    owner=result["CredentialOwner"],
                    description=result["Description"],
                )
