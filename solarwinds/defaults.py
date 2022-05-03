NODE_DEFAULT_POLLERS = {
    "icmp": [
        "N.Status.ICMP.Native",
        "N.ResponseTime.ICMP.Native",
    ],
    "snmp": [
        "N.AssetInventory.Snmp.Generic",
        "N.Cpu.SNMP.HrProcessorLoad",
        "N.Details.SNMP.Generic",
        "N.Memory.SNMP.NetSnmpReal",
        "N.ResponseTime.SNMP.Native",
        "N.Routing.SNMP.Ipv4CidrRoutingTable",
        "N.Topology_Layer3.SNMP.ipNetToMedia",
        "N.Uptime.SNMP.Generic",
    ],
}
EXCLUDE_CUSTOM_PROPS = [
    "DisplayName",
    "NodeID",
    "InstanceType",
    "Uri",
    "InstanceSiteId",
]