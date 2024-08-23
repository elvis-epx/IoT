import machine

import network
machine.test_mocks['network'] = network

import espnow
machine.test_mocks['espnow'] = espnow

from uumqtt import simple2
machine.test_mocks['mqtt'] = simple2
