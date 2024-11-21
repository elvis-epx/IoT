print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from rx433.sensor import KeyfobRX
from epx.mqtt import MQTT
from epx.ota import mqtt_ota_start
from rx433.service import *

config = Config()
config.data['flavor'] = 'rx433'
watchdog = Watchdog(config)
net = Net(config)

mqtt = MQTT(config, net, watchdog)
mqtt_ota_start(mqtt, config)

mqttservice = KeyfobService()
sensor = KeyfobRX(config, mqttservice)

mqtt.pub(mqttservice)
mqtt.pub(KeyfobStats(sensor))

try:
    loop.run()
except:
    sensor.stop()
    raise
