from pysolarwinds import Solarwinds
from config import sw_args
import ipdb
from pprint import pprint

sw = Solarwinds(**sw_args)
#pprint(sw.node.get(ip='10.12.104.97'))
sw.node.create(ip='1.2.3.4', hostname='my_test_host')
ipdb.set_trace()
