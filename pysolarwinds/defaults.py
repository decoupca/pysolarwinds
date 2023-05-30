# defaults based on:
# https://github.com/pysolarwinds/orionsdk-python/blob/master/samples/discover_one_node.py
NODE_DISCOVERY_JOB_TIMEOUT_SECONDS = 600
NODE_DISCOVERY_SEARCH_TIMEOUT_MILLISECONDS = 5000
NODE_DISCOVERY_SNMP_TIMEOUT_MILLISECONDS = 5000
NODE_DISCOVERY_SNMP_RETRIES = 3
NODE_DISCOVERY_REPEAT_INTERVAL_MILLISECONDS = 1800
NODE_DISCOVERY_SNMP_PORT = 161
NODE_DISCOVERY_HOP_COUNT = 0
NODE_DISCOVERY_PREFERRED_SNMP_VERSION = "SNMP2c"  # misnomer, leave as-is for snmpv3
NODE_DISCOVERY_DISABLE_ICMP = False
NODE_DISCOVERY_ALLOW_DUPLICATE_NODES = False
NODE_DISCOVERY_IS_AUTO_IMPORT = True
NODE_DISCOVERY_IS_HIDDEN = False

EXCLUDE_CUSTOM_PROPS = [
    "DisplayName",
    "NodeID",
    "InstanceType",
    "Uri",
    "InstanceSiteId",
    "Description",
]

# In most cases, resource import takes 10-90 seconds. But
# under certain conditions, e.g. high latency nodes with many resources,
# import can take exceptionally long. Since an incomplete resource import
# will likely leave a node in an error state, it's wise to be very generous
# in this timeout value.
IMPORT_RESOURCES_TIMEOUT = 600

# To prevent triggering false positive alerts during resource import,
# it makes sense to unmanage the node during the process. When the import
# completes, the node will be re-managed right away. But, if the resource
# import fails (e.g, due to timeout or other unhandled exception), the node
# will remain unmanaged indefinitely without this failsafe. In testing we found
# that remediating nodes with failed imports can take longer than expected,
# so it's sensible to give ourselves plenty of time before the node re-manages
# itself.
IMPORT_RESOURCES_UNMANAGE_NODE_DAYS = 1
