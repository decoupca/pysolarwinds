# defaults based on:
# https://github.com/solarwinds/orionsdk-python/blob/master/samples/discover_one_node.py
NODE_DISCOVERY_JOB_TIMEOUT_SECONDS = 120
NODE_DISCOVERY_SEARCH_TIMEOUT_MILLISECONDS = 5000
NODE_DISCOVERY_SNMP_TIMEOUT_MILLISECONDS = 5000
NODE_DISCOVERY_SNMP_RETRIES = 2
NODE_DISCOVERY_REPEAT_INTERVAL_MILLISECONDS = 1800
NODE_DISCOVERY_SNMP_PORT = 161
NODE_DISCOVERY_HOP_COUNT = 0
NODE_DISCOVERY_PREFERRED_SNMP_VERSION = "SNMP2c"  # misnomer, leave as-is for snmpv3
NODE_DISCOVERY_DISABLE_ICMP = False
NODE_DISCOVERY_ALLOW_DUPLICATE_NODES = False
NODE_DISCOVERY_IS_AUTO_IMPORT = True
NODE_DISCOVERY_IS_HIDDEN = False

NODE_DEFAULT_POLLERS = {
    "icmp": [
        "N.Status.ICMP.Native",
        "N.ResponseTime.ICMP.Native",
    ],
    "snmp": [
        "N.Status.ICMP.Native",
        "N.ResponseTime.ICMP.Native",
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

NODE_CISCO_POLLERS = [
    "N.Cpu.SNMP.CiscoGen3",
    "N.Details.SNMP.Generic",
    "N.EnergyWise.SNMP.Cisco",
    "N.HardwareHealthMonitoring.SNMP.NPM.Cisco",
    "N.Memory.SNMP.CiscoGen4",
    "N.MulticastRouting.SNMP.MulticastRoutingTable",
    "N.ResponseTime.ICMP.Native",
    "N.ResponseTime.SNMP.Native",
    "N.Routing.SNMP.Ipv4CidrRoutingTable",
    "N.RoutingNeighbor.SNMP.BGP",
    "N.RoutingNeighbor.SNMP.OSPF",
    "N.Status.ICMP.Native",
    "N.Status.SNMP.Native",
    "N.SwitchStack.SNMP.Cisco",
    "N.Topology_CDP.SNMP.cdpCacheTable",
    "N.Topology_LLDP.SNMP.lldpRemoteSystemsData",
    "N.Topology_Layer2.SNMP.Dot1dTpFdb",
    "N.Topology_Layer3.SNMP.ipNetToMedia",
    "N.Topology_Layer3_IpRouting.SNMP.ipCidrRouter",
    "N.Topology_PortsMap.SNMP.Dot1dBase",
    "N.Topology_Vlans.SNMP.VtpVlan",
    "N.Uptime.SNMP.Generic",
    "N.VRFRouting.SNMP.MPLSVPNStandard",
]

EXCLUDE_CUSTOM_PROPS = [
    "DisplayName",
    "NodeID",
    "InstanceType",
    "Uri",
    "InstanceSiteId",
    "Description",
]

IMPORT_RESOURCES_TIMEOUT = 30
