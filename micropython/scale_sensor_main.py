print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.netnow import NetNowPeripheral
from scale_sensor.sensor import Sensor
from scale_sensor.service import Service
from machine import Pin

config = Config()
watchdog = Watchdog(config, True)
netnow = NetNowPeripheral(config, watchdog)
sensor = Sensor(config, watchdog)
srv = Service(config, watchdog, netnow, sensor)

loop.run()
