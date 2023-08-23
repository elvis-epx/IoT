print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from epx.nvram import NVRAM
from switch.driver import *
from switch.actuator import Switch
from switch.sensor import Manual

config = Config()
watchdog = Watchdog(config)
net = Net(config)
mqtt = MQTT(config, net, watchdog)
nvram = NVRAM("switch")

print(config.data)
poll = int(config.data["poll"])
debounce = int(config.data["debounce"])

if "direct4" == config.data["driver"]:
    driver = Direct4()

switches = [ Switch(nvram, mqtt, driver, i) for i in range(0, driver.outputs) ]
bridge = Manual(nvram, mqtt, driver, switches, poll, debounce)

loop.run()
