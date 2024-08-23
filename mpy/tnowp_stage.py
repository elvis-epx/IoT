import machine

import network
machine.test_mocks['network'] = network

import espnow
machine.test_mocks['espnow'] = espnow
