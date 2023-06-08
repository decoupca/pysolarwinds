"""Credentials query."""
from pypika import MSSQLQuery, Table

TABLE = Table("Orion.Credential")
FIELDS = ("ID", "Name", "Description", "CredentialType", "CredentialOwner", "Uri")
QUERY = MSSQLQuery.from_(TABLE).select(*FIELDS)
