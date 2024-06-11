print("*** START ***")

from epx import loop
from epx.config import Config
from epx.watchdog import Watchdog
from epx.net import Net
from epx.mqtt import MQTT
from h2o.service import VolUnit, CoarseLevelPct, CoarseLevelVol, PumpedAfterLevelChange, \
                            EstimatedLevelVol, EstimatedLevelStr, Malfunction, Flow
from h2o.sensor import LevelMeter, FlowMeter 
from h2o.actuator import Display
from machine import I2C, Pin

config = Config()
watchdog = Watchdog(config)
i2c = I2C(0, sda=Pin(21), scl=Pin(22))
net = Net(config)

flowmeter = FlowMeter(config)
levelmeter = LevelMeter(config, i2c, flowmeter)

mqtt = MQTT(config, net, watchdog)
mqtt.pub(VolUnit(config))
mqtt.pub(CoarseLevelPct(levelmeter))
mqtt.pub(CoarseLevelVol(levelmeter))
mqtt.pub(PumpedAfterLevelChange(flowmeter))
mqtt.pub(EstimatedLevelVol(levelmeter))
mqtt.pub(EstimatedLevelStr(levelmeter))
mqtt.pub(Flow(flowmeter))
mqtt.pub(Malfunction(levelmeter))

display = Display(config, i2c, net, mqtt, levelmeter, flowmeter)
    
loop.run()
