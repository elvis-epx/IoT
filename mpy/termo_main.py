print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from epx.ota import mqtt_ota_start

from termo.sensor import Sensor
from termo.service import Temperatures

config = Config()
config.data['flavor'] = 'termo'
watchdog = Watchdog(config)

net = Net(config)

mqtt = MQTT(config, net, watchdog)
mqtt_ota_start(mqtt, config)
sensor = Sensor(mqtt, Temperatures)
mqtt.pub(Malfunction(sensor))

loop.run()
