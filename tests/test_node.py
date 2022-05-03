from .fixtures import sw

node = sw.orion.node(ip_address="172.16.1.1")


def test_node():
    assert node.ip == "172.16.1.1"
    assert node.exists() == False
