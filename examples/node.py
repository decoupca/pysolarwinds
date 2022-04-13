from pprint import pprint

import ipdb
from config import sw_args

from pysolarwinds import Solarwinds

sw = Solarwinds(**sw_args)

# pprint(sw.node.details(ip='10.12.104.97'))
uri = sw.node.create(ip="172.16.1.1", hostname="Cantina")
# you can update nodes by IP or hostname, but passing the uri (if you have it) saves an API call
sw.node.update(uri=uri, custom_properties={"site": "Mos Eisley", "region": "Tatooine"})
# sw.node.delete('172.16.1.1')
