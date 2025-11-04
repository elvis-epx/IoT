import machine

import network
machine.test_mocks['network'] = network

from uumqtt import simple2
machine.test_mocks['mqtt'] = simple2

from third import ssd1306, mcp23017
machine.test_mocks['ssd1306'] = ssd1306
machine.test_mocks['mcp23017'] = mcp23017
