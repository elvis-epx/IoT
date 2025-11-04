print("*** START ***")

from epx import loop
from epx.config import Config
from epx.nvram import NVRAM
from epx.watchdog import Watchdog
from epx.netnowp import NetNowPeripheral
from tnowp.service import Service
from machine import Pin

config = Config()
config.data['flavor'] = 'tnowp'
nvram = NVRAM("tnowp")
watchdog = Watchdog(config, True)
netnow = NetNowPeripheral(config, nvram, watchdog)
srv = Service(config, watchdog, netnow)

loop.run()
