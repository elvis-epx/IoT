print("*** START ***")

from epx import loop
from epx.loop import Task, MILISSECONDS
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from epx.io import SerialIO
from switch.actuator import Switch, Display
from switch.sensor import Manual
from switch.service import SwitchPub, SwitchSub
from machine import I2C, Pin

config = Config()
watchdog = Watchdog(config)
i2c = I2C(0, sda=Pin(21), scl=Pin(22))
gpio = SerialIO(i2c)
net = Net(config)
mqtt = MQTT(config, net, watchdog)

switches = {}

print(config.data)
names = [x for x in config.data["switches"].split(",") if x]
inputmodes = [x for x in config.data["inputmodes"].split(",") if x]
switchmodes = [x for x in config.data["switchmodes"].split(",") if x]

for i in range(0, min(len(inputmodes), len(names), len(switchmodes))):
    name = names[i]
    inputmode = inputmodes[i]
    switchmode = switchmodes[i]

    manual = Manual(name, gpio, i, inputmode, switchmode)
    switch = Switch(name, gpio, i, inputmode, switchmode, manual)
    switches[name] = switch
    mqtt.pub(SwitchPub(name, switch))
    mqtt.sub(SwitchSub(name, switch))

def handle_gpio(_):
    gpio.eval() # also does output
    for name in switches.keys():
        switches[name].manual.eval()

# FIXME test x initial gpio state
Task(True, "handle_gpio", handle_gpio, 35 * MILISSECONDS)

display = Display(i2c, switches, net, mqtt)

loop.run()
