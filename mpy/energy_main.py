print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from energy.sensor import Sensor
from epx.mqtt import MQTT
from epx.ota import mqtt_ota_start
from energy.service import *

config = Config()
config.data['flavor'] = 'energy'
watchdog = Watchdog(config)
sensor = Sensor(config)
net = Net(config)

mqtt = MQTT(config, net, watchdog)
mqtt_ota_start(mqtt, config)
mqtt.pub(Voltage(sensor))
mqtt.pub(VoltageNow(sensor))
mqtt.pub(VoltageMin(sensor))
mqtt.pub(VoltageMax(sensor))
mqtt.pub(Current(sensor))
mqtt.pub(CurrentNow(sensor))
mqtt.pub(CurrentMax(sensor))
mqtt.pub(Power(sensor))
mqtt.pub(PowerNow(sensor))
mqtt.pub(VA(sensor))
mqtt.pub(VANow(sensor))
mqtt.pub(Malfunction(sensor))

mqtt.sub(Ticker(sensor))

loop.run()
