print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from energy.sensor import Sensor
from epx.mqtt import MQTT
from energy.service import Voltage, Current, PowerFactor, Energy, Malfunction, Ticker

config = Config()
watchdog = Watchdog(config)
sensor = Sensor()
net = Net(config)

mqtt = MQTT(config, net, watchdog)
mqtt.pub(Voltage(sensor))
mqtt.pub(Current(sensor))
mqtt.pub(PowerFactor(sensor))
mqtt.pub(Energy(sensor))
mqtt.pub(Malfunction(sensor))
ticker = Ticker(sensor)

loop.run()
