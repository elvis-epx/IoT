print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from switch.driver import *
from switch.actuator import Switch
from switch.sensor import Manual

config = Config()
watchdog = Watchdog(config)
net = Net(config)
mqtt = MQTT(config, net, watchdog)

print(config.data)
poll = int(config.data["poll"])
debounce = int(config.data["debounce"])

if "direct4" == config.data["driver"]:
    driver = Direct4()

switches = [ Switch(mqtt, driver, i) for i in range(0, driver.outputs) ]
bridge = Manual(mqtt, driver, switches, poll, debounce)

loop.run()
