print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from weather.sensor import Sensor
from weather.actuator import Display
from epx.mqtt import MQTT
from epx.ota import mqtt_ota_start
from weather.service import Temperature, Humidity, Pressure, Malfunction
from machine import I2C, Pin

config = Config()
config.data['flavor'] = 'weather'
watchdog = Watchdog(config)
i2c = I2C(0, sda=Pin(21), scl=Pin(22))
sensor = Sensor(i2c)

net = Net(config)

mqtt = MQTT(config, net, watchdog)
mqtt_ota_start(mqtt, config)
mqtt.pub(Temperature(sensor))
mqtt.pub(Humidity(sensor))
mqtt.pub(Pressure(sensor))
mqtt.pub(Malfunction(sensor))

display = Display(config, i2c, sensor)
    
loop.run()
