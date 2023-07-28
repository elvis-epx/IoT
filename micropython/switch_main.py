print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from epx.io import SerialIO
from switch.service import SwitchPub, SwitchSub
from switch.actuator import Switch, Display
from switch.sensor import Manual
from machine import I2C, Pin

config = Config()
watchdog = Watchdog(config)
i2c = I2C(0, sda=Pin(21), scl=Pin(22))
gpio = SerialIO(i2c)
net = Net(config)
mqtt = MQTT(config, net, watchdog)

display = Display(i2c, switches, net, mqtt)

switches = {}

names = [x for x in config["switches"].split(" ") if x]
inputmodes = [x for x in config["inputmodes"].split(" ") if x]
inputpins = [x for x in config["inputs"].split(" ") if x]
outputpins = [x for x in config["outputs"].split(" ") if x]

for i in range(0, len(names)):
    name = names[i]
    inputmode = inputmodes[i]
    inputpin = inputpin[i]
    outputpin = outputin[i]

    manual = Manual(name, gpio, inputpin, inputmode)
    switch = Switch(name, gpio, outputpin, manual)
    switches[name] = switch
    mqtt.pub(SwitchPub(name, switch))
    mqtt.sub(SwitchSub(name, switch))

loop.run()
