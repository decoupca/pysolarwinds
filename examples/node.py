from pysolarwinds import Solarwinds
from config import sw_args
import ipdb
from pprint import pprint

sw = Solarwinds(**sw_args)
#pprint(sw.node.get(ip='10.12.104.97'))
#uri = sw.node.create(ip='172.16.1.1', hostname='cantina', custom_properties={'site': 'mos_eisley', 'region': 'tatooine'})
pprint(sw.node.delete('172.16.1.1'))
ipdb.set_trace()
