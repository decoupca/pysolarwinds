from pysolarwinds.models import BaseModel

class Node(BaseModel):
    def _get_uri(self, hostname=None, ip=None):
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
            msg = f"SWQL query below returned no results. Check hostname/ip.\n{query}"
            raise ValueError(msg)
        if len(results) > 1:
            msg = (
                f"SWQL query below returned {len(results)} results. "
                f"Try a different combination of hostname/ip, or remove duplicates in Solarwinds."
                f"\n{query}"
            )
            raise ValueError(msg)
        else:
            return results[0]["uri"]

    def create(self, hostname=None, ip=None, properties=None, custom_properties=None):
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
        props.update(properties)
        props.update({'IPAddres': ip})
        if hostname:
            props.update({'Caption': hostname})
        if custom_properties:
            props.update({'CustomProperties': custom_properties})
        return self.swis.create('Orion.Nodes', **props)

    def delete(self, hostname=None, ip=None, uri=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        return self.swis.delete(uri)

    def exists(self, hostname=None, ip=None):
        if self._get_uri(hostname=hostname, ip=ip):
            return True
        else:
            return False

    def get(self, hostname=None, ip=None, uri=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        return self.swis.read(uri)['results']

    def update(self, hostname=None, ip=None, uri=None, properties=None, custom_properties=None):
        if uri is None:
            uri = self._get_uri(hostname=hostname, ip=ip)
        if properties:
            if hostname:
                properties.update({'Caption': hostname})
            if ip:
                properties.update({'IPAddress': ip})
            swis.update(uri, **properties)
        if custom_properties:
            swis.update(f'{uri}/CustomProperties', **custom_properties)


