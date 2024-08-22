import machine

import network
machine.test_mocks['network'] = network

import espnow
machine.test_mocks['espnow'] = espnow

from third import hx711
machine.test_mocks['hx711'] = hx711
