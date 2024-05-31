print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.netnow import NetNowPeripheral
from scale_sensor.sensor import Sensor
from scale_sensor.service import Service
from machine import Pin

config = Config()
watchdog = Watchdog(config)
netnow = NetNowPeripheral(config)
sensor = Sensor(config)
srv = Service(config, netnow, sensor)

loop.run()
