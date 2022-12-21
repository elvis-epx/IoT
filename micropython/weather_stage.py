import machine

import network
machine.test_mocks['network'] = network

from uumqtt import simple2
machine.test_mocks['mqtt'] = simple2

from third import bme280, hdc1080
machine.test_mocks['bme280'] = bme280
machine.test_mocks['hdc1080'] = hdc1080
