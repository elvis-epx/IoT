print("*** START ***")

from epx import loop
from epx.config import Config
from epx.nvram import NVRAM
from epx.watchdog import Watchdog
from epx.net import Net
from epx.netnow import NetNowCentral
from epx.mqtt import MQTT, MQTTSub
from scale_manager.forwarder import Forwarder

config = Config()
nvram = NVRAM("scale_manager")
watchdog = Watchdog(config)
net = Net(config)
netnow = NetNowCentral(config, nvram, net)
mqtt = MQTT(config, net, watchdog)
forwarder = Forwarder(config, netnow, mqtt)

loop.run()
