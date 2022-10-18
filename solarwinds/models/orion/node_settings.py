from solarwinds.endpoints.orion.credential import OrionCredential


class OrionNodeSettings(object):
    def __init__(self, node):
        self.node = node
        self.swis = node.swis
        self._settings = []

        self.snmpv3_ro_cred = None
        self.snmpv3_rw_cred = None

        query = (
            "SELECT SettingName, SettingValue, NodeSettingID "
            f"FROM Orion.NodeSettings WHERE NodeID = '{self.node.id}'"
        )
        settings = self.swis.query(query)
        if settings is not None:
            for setting in settings:
                name = setting["SettingName"]
                value = setting["SettingValue"]

                if name in ["ROSNMPCredentialID", "RWSNMPCredentialID"]:
                    cred = OrionCredential(
                        swis=self.swis, node_id=self.node.id, id=value
                    )
                    self._settings.append(cred)
                    if name == "ROSNMPCredentialID":
                        if cred.credential_type.endswith("SnmpCredentialsV3"):
                            self.snmpv3_ro_cred = cred
                            self.node.snmpv3_ro_cred_name = cred.name
                            self.node.snmpv3_ro_cred_id = cred.id
                    if name == "RWSNMPCredentialID":
                        if cred.credential_type.endswith("SnmpCredentialsV3"):
                            self.snmpv3_rw_cred = cred
                            self.node.snmpv3_rw_cred_name = cred.name
                            self.node.snmpv3_rw_cred_id = cred.id

    def __getitem__(self, item):
        return self._settings[item]

    def __repr__(self):
        return str(self._settings)
