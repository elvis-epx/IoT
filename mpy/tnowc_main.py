print("*** START ***")

from epx import loop
from epx.config import Config
from epx.nvram import NVRAM
from epx.watchdog import Watchdog
from epx.net import Net
from epx.netnowc import NetNowCentral
from epx.mqtt import MQTT
from epx.ota import mqtt_ota_start
from tnowc.forwarder import Forwarder

config = Config()
config.data['flavor'] = 'tnowc'
nvram = NVRAM("tnowc")
watchdog = Watchdog(config)
net = Net(config)
netnow = NetNowCentral(config, nvram, net)
mqtt = MQTT(config, net, watchdog)
mqtt_ota_start(mqtt, config)
forwarder = Forwarder(config, netnow, mqtt)

loop.run()
