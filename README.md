# pysolarwinds

A modern Python API for the SolarWinds Information Service (SWIS). Requires Python 3.9+

**WARNING**: This API is under heavy development and is likely to introduce breaking changes. You can expect a stable API in the 1.0.0 release.

## Install

```
pip install git+https://github.com/decoupca/pysolarwinds@master
```

## Quick start

```python
>>> import pysolarwinds
>>> # Initialize the main client
>>> sw = pysolarwinds.client(host='solarwinds.example.net', username='swuser', password='s3cr3t', validate=False)
>>> # Retrieve a node
>>> node = sw.orion.nodes.get(caption='my-node')
>>> # Explore node properties
>>> node
OrionNode(caption='my-node')
>>> node.ip
'172.18.64.4'
>>> node.uptime
datetime.timedelta(days=268, seconds=62125, microseconds=376991)
>>> node.pollers
[OrionPoller(node=OrionNode(caption='my-node'), poller_type='N.ResponseTime.ICMP.Native'), ...]
>>> node.polling_method
'icmp'
>>> # Update node properties
>>> node.caption = 'my-node-2'
>>> node.polling_method = 'snmp'
>>> node.snmp_version = 2
>>> node.snmpv2_ro_community = 'r0-c0mmun1ty'
>>> node.snmpv2_rw_community = 'rw-c0mmun1ty'
>>> node.save()  # Returns None if successful
```

## Advanced Usage

### `SolarWindsClient` options

You can also pass certificate validation and timeout settings to `pysolarwinds.client()`:
```python
sw = pysolarwinds.client(
    host='solarwinds.example.net',
    username='sw-user',
    password='s3cr3t',
    verify='/path/to/ca-cert.pem',
    timeout=120.0
)
```

### HTTP fine-tuning

If you need further control over the HTTP client, you can replace `sw.swis.client` with your own instance of [`httpx.Client()`](https://www.python-httpx.org/api/#client). Be sure to include the `auth` parameter and the `Content-Type: application/json` header.
```python
import httpx
client = httpx.Client(
    auth=('my-user', 's3cr3t'),
    timeout=httpx.Timeout(connect=15.0, pool=30.0, read=120.0, write=120.0),
    headers={b"Content-Type": b"application/json"},
    limits=httpx.Limits(max_keepalive_connections=None, max_connections=None),
    verify='/path/to/ca-cert.pem',
)
sw.swis.client = client
```

### Manually construct objects

The `SolarWindsClient` returned by `pysolarwinds.client()` provides a convenient way to create and retrie SolarWinds objects. This is the recommended approach, as it handles `SWISClient` creation and insertion, and more gracefully handles certain validation issues. If you prefer, you can also construct objects directly:
```python
>>> from pysolarwinds.swis import SWISClient
>>> from pysolarwinds.endpoints.orion.nodes import OrionNode
>>> swis = SWISClient(host='solarwinds.example.net', username='sw-user', password='s3cr3t')
>>> node = OrionNode(swis=swis, caption='my-node')
>>> node
OrionNode(caption='my-node')
```
