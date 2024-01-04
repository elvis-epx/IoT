print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from relay.service import RelayPub, RelaySub
from relay.actuator import Relay, Display
from machine import I2C, Pin

config = Config()
watchdog = Watchdog(config)
i2c = I2C(0, sda=Pin(21), scl=Pin(22))
net = Net(config)

# TODO move this to configuration
timeouts = [600, 24 * 3600, 24 * 3600, 24 * 3600]
relays = []
mqtt = MQTT(config, net, watchdog)
for i in range(0, 4):
    relay = Relay(i, timeouts[i])
    relays.append(relay)
    mqtt.pub(RelayPub(i, relay))
    mqtt.sub(RelaySub(i, relay))

display = Display(i2c, relays, net, mqtt)
    
loop.run()
