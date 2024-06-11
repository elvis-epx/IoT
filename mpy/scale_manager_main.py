print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.netnow import NetNowManager
from epx.mqtt import MQTT
from scale_manager.forwarder import Forwarder

config = Config()
watchdog = Watchdog(config)
net = Net(config)
netnow = NetNowManager(config, net)
mqtt = MQTT(config, net, watchdog)
forwarder = Forwarder(config, netnow, mqtt)

loop.run()
