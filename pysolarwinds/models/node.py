from pysolarwinds.models import BaseModel
from pysolarwinds.core.exceptions import SWObjectNotFoundError, SWNonUniqueResultError

class Node(BaseModel):
    def _get_uri(self, ip=None, hostname=None):
        if hostname is None and ip is None:
            raise ValueError("Must provide hostname, IP, or both")
        where = []
        if hostname:
            where.append(f"Caption = '{hostname}'")
        if ip:
            where.append(f"IPAddress = '{ip}'")
        where_clause = " AND ".join(where)
        query = f"SELECT Uri AS uri FROM Orion.Nodes WHERE {where_clause}"
        results = self.swis.query(query)["results"]
        if not results:
            msg = f"Node not found. heck hostname/ip.\nSWQL query: {query}"
            raise SWObjectNotFoundError(msg)
        if len(results) > 1:
            msg = (
                f"Got {len(results)} results. Try a different combination of hostname/ip, "
                f"or remove duplicates in Solarwinds.\nSWQL query: {query}"
            )
            raise SWNonUniqueResultError(msg)
        else:
            return results[0]["uri"]

    def create(self, ip=None, hostname=None, properties=None, custom_properties=None):
        ip = ip or properties.get('IPAddress')
        hostname = hostname or properties.get('Caption')
        if ip is None:
            raise ValueError('Must provide polling IP as either ip arg, or "IPAddress" key in properties arg')
        props = {
            'EngineID': 1,
            'ObjectSubType': 'SNMP',
            'SNMPVersion': 2,
        }
        # update/overwrite default props with provided properties
        if properties:
            props.update(properties)
        props.update({'IPAddress': ip})
        if hostname:
            props.update({'Caption': hostname})
        uri = self.swis.create('Orion.Nodes', **props)
        if custom_properties:
            self.update(uri=uri, custom_properties=custom_properties)
        return uri

    def delete(self, ip=None, hostname=None, uri=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        return self.swis.delete(uri)

    def exists(self, ip=None, hostname=None):
        if self._get_uri(hostname=hostname, ip=ip):
            return True
        else:
            return False

    def get(self, ip=None, hostname=None, uri=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        return self.swis.read(uri)

    def update(self, ip=None, hostname=None, properties=None, custom_properties=None, uri=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        if properties:
            if hostname:
                properties.update({'Caption': hostname})
            if ip:
                properties.update({'IPAddress': ip})
            self.swis.update(uri, **properties)
        if custom_properties:
            self.swis.update(f'{uri}/CustomProperties', **custom_properties)


