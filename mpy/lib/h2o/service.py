from epx.mqtt import MQTTPub
from epx.loop import SECONDS, MINUTES


class VolUnit(MQTTPub):
    def __init__(self, config):
        self.unit = config.data['unit']
        MQTTPub.__init__(self, "stat/%s/VolUnit", 1000 * MINUTES, 30 * MINUTES, False)

    def gen_msg(self):
        return self.unit


class CoarseLevelPct(MQTTPub):
    def __init__(self, levelmeter):
        self.levelmeter = levelmeter
        MQTTPub.__init__(self, "stat/%s/CoarseLevelPct", 1 * SECONDS, 10 * MINUTES, False)

    def gen_msg(self):
        v = self.levelmeter.coarse_level_pct()
        if v is None:
            return None
        return "%.0f" % v


class CoarseLevelVol(MQTTPub):
    def __init__(self, levelmeter):
        self.levelmeter = levelmeter
        MQTTPub.__init__(self, "stat/%s/CoarseLevelVol", 1 * SECONDS, 10 * MINUTES, False)

    def gen_msg(self):
        v = self.levelmeter.coarse_level_vol()
        if v is None:
            return None
        return "%.0f" % v


class EstimatedLevelVol(MQTTPub):
    def __init__(self, levelmeter):
        self.levelmeter = levelmeter
        MQTTPub.__init__(self, "stat/%s/EstimatedLevelVol", 10 * SECONDS, 10 * MINUTES, False)

    def gen_msg(self):
        v = self.levelmeter.estimated_level_vol()
        if v is None:
            return None
        return "%.0f" % v


class EstimatedLevelStr(MQTTPub):
    def __init__(self, levelmeter):
        self.levelmeter = levelmeter
        MQTTPub.__init__(self, "stat/%s/EstimatedLevelStr", 10 * SECONDS, 10 * MINUTES, False)

    def gen_msg(self):
        s = self.levelmeter.estimated_level_str()
        if s is None:
            return None
        return s


class Flow(MQTTPub):
    def __init__(self, flowmeter):
        self.flowmeter = flowmeter
        MQTTPub.__init__(self, "stat/%s/Flow", 10 * SECONDS, 30 * MINUTES, False)

    # Make sure rate is republished as long as it is positive, even if unchanged
    def pub_condition(self, force, oldrate, newrate):
        return force or oldrate != newrate or newrate != b'0.0'

    def gen_msg(self):
        rate = self.flowmeter.rate()
        # rate can't be None, only 0
        return "%.1f" % rate


class PumpedAfterLevelChange(MQTTPub):
    def __init__(self, flowmeter):
        self.flowmeter = flowmeter
        MQTTPub.__init__(self, "stat/%s/PumpedAfterLevelChange", 10 * SECONDS, 30 * MINUTES, False)

    def gen_msg(self):
        # can't be None, only 0
        v = self.flowmeter.pumped_since_level_change()
        return "%.1f" % v


class Malfunction(MQTTPub):
    def __init__(self, levelmeter):
        self.levelmeter = levelmeter
        MQTTPub.__init__(self, "stat/%s/Malfunction", 1 * SECONDS, 30 * MINUTES, False)

    def gen_msg(self):
        return "%d" % self.levelmeter.malfunction()


class LevelSensorMap(MQTTPub):
    def __init__(self, levelmeter):
        self.levelmeter = levelmeter
        MQTTPub.__init__(self, "stat/%s/LevelSensorMap", 1 * SECONDS, 30 * MINUTES, False)

    def gen_msg(self):
        return ",".join(["%d" % n for n in self.levelmeter.sensormap()])
