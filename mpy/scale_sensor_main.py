print("*** START ***")

from epx import loop
from epx.config import Config
from epx.nvram import NVRAM
from epx.watchdog import Watchdog
from epx.netnowp import NetNowPeripheral
from scale_sensor.sensor import Sensor
from scale_sensor.service import Service
from machine import Pin

config = Config()
nvram = NVRAM("scale_sensor")
watchdog = Watchdog(config, True)
netnow = NetNowPeripheral(config, nvram, watchdog)
sensor = Sensor(config, watchdog)
srv = Service(config, watchdog, netnow, sensor)

try:
    loop.run()
finally:
    netnow.stop()
