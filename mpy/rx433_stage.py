import machine

import network
machine.test_mocks['network'] = network

from uumqtt import simple2
machine.test_mocks['mqtt'] = simple2
