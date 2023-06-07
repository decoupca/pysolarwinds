from typing import Optional

from pysolarwinds.endpoints.orion.credentials import Credential


class SNMPv2Credential(Credential):
    def update(self, community: str, name: Optional[str] = None) -> None:
        """
        Update SNMPv1/2 credential community and optionally name.

        The way the SWIS API is built, it is not possible to only update the
        name without also providing the community string. When updating the name only,
        passing the community is required, but it need not be different.

        Arguments:
            community: Community string to update.
            name: Credential name to update. If omitted, will use current name.
        """
        if name is None:
            name = self.name
        self.swis.invoke(
            "Orion.Credential", "UpdateSNMPCredentials", self.id, name, community
        )

    def __repr__(self) -> str:
        return f"SNMPv2Credential(name='{self.name}')"
