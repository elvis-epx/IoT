from epx.loop import Task, SECONDS, MINUTES, Shortcronometer
from epx import loop
from third import mcp23017
from machine import Pin

class FlowMeter:
    def __init__(self, config):
        # in pulses/sec when flow rate = 1 unit/min
        self.pulserate = float(config.data['flowpulserate'])
        print("config: flow pulse rate %f" % self.pulserate)
        self.single_pulse_vol = (1.0 / 60.0) / self.pulserate # volume of a single pulse
        # maximum valid flow, convert L/min to pulses/s
        self.maxflow = float(config.data['maxflow']) * self.pulserate
        self._pulses = 0
        self.pulses = 0
        self.pulses_since_level_change = 0
        self.latest_rate = 0.0 # in units/minute
        self.malfunction_value = 0

        self.task = Task(True, "flowmeter", self.eval, 1 * SECONDS)
        self.task_m = Task(True, "flowmeter", self.clear_malfunction, 10 * MINUTES)
        self.cronometer = Shortcronometer()

        self.pin = Pin(14, Pin.IN)
        self.pin.irq(trigger = Pin.IRQ_RISING, handler=self.irq)

    def irq(self, _):
        self._pulses += 1

    def clear_malfunction(self, _):
        self.malfunction_value = 0

    def eval(self, _):
        p, self._pulses = self._pulses, 0
        # Note: the following test depends on eval() being called every 1s
        if p > self.maxflow:
            self.malfunction_value = 0x10
            p = 0
        self.pulses += p
        self.pulses_since_level_change += p

        elapsed = self.cronometer.elapsed()
        if elapsed > 5 * SECONDS:
            self.cronometer.restart()
            p, self.pulses = self.pulses, 0
            self.latest_rate = p * self.single_pulse_vol / (elapsed / (MINUTES + 0.0))

    def rate(self):
        return self.latest_rate

    def pumped_since_level_change(self):
        return self.pulses_since_level_change * self.single_pulse_vol

    def level_changed(self):
        self.pulses_since_level_change = 0

    def malfunction(self):
        return self.malfunction_value

class LevelMeter:
    def __init__(self, config, i2c, flowmeter):
        self.i2c = i2c
        self.flowmeter = flowmeter
        self.capacity = float(config.data['capacity'])
        self.unit = config.data['unit']
        print("config: capacity %f%s" % (self.capacity, self.unit))
        sensors = config.data['levelsensors']
        print("config: sensors", sensors)
        self.sensors = [ float(x) for x in sensors.split(",") ]
        self.sensors_bitmask = (1 << len(self.sensors)) - 1
        print("config: bitmask %x" % self.sensors_bitmask)

        self.latest_bitmap = 0xffffffff
        self.debounce_bitmaps = [0]
        self.debounce = 4
        self.level = -1.0
        self.malfunction_bitmap = 0x00

        self.mcp = None
        Task(True, "levelstart", self.start_mcp, 10 * MINUTES).advance()
        Task(True, "level", self.eval, 1 * SECONDS)

    def start_mcp(self, _):
        if self.mcp:
            return

        try:
            self.mcp = mcp23017.MCP23017(self.i2c, 0x20)
            self.mcp.porta.mode = 0xff
            self.mcp.porta.pullup = 0xff
            self.mcp.portb.mode = 0xff
            self.mcp.portb.pullup = 0xff
            self.malfunction_bitmap &= ~0x02
            print("level meter: mcp active")
        except OSError:
            print("level meter: mcp failed, retry in 10 min")
            self.mcp = None
            self.level = 100.0 # guarantee that observer stops filling up
            self.malfunction_bitmap |= 0x02

    def eval(self, _):
        if not self.mcp:
            return

        try:
            bitmap = self.mcp.porta.gpio << 8 | self.mcp.portb.gpio
            self.malfunction_bitmap &= ~0x04
        except OSError:
            print("level meter: mcp read fail")
            self.mcp = None
            self.level = 100.0 # guarantee that observer stops filling up
            self.malfunction_bitmap |= 0x04
            return

        bitmap &= self.sensors_bitmask

        self.debounce_bitmaps.pop(0)
        while len(self.debounce_bitmaps) < self.debounce:
            self.debounce_bitmaps.append(bitmap)
        debounced = True
        for i in range(0, len(self.debounce_bitmaps) - 1):
            debounced = debounced and self.debounce_bitmaps[i] == self.debounce_bitmaps[i+1]
        if not debounced:
            return

        if self.latest_bitmap == bitmap:
            return
        self.latest_bitmap = bitmap

        jump, err = False, False
        new_level = 0.0
        for i, pct in enumerate(self.sensors):
            mask = 1 << i
            bit = bitmap & mask
            bit = not bit # pull-up logic
            if bit:
                new_level = pct
                err = err or jump
            else:
                jump = True

        if new_level != self.level:
            self.flowmeter.level_changed()
            self.level = new_level

        if err:
            self.malfunction_bitmap |= 0x01
        else:
            self.malfunction_bitmap &= ~0x01
            

    def coarse_level_pct(self):
        if self.level < 0:
            return None
        return self.level

    def coarse_level_vol(self):
        if self.level < 0:
            return None
        return self.level * self.capacity / 100.0

    def estimated_level_vol(self):
        if self.level < 0:
            return None
        return self.coarse_level_vol() + self.flowmeter.pumped_since_level_change()

    def estimated_level_str(self):
        if self.level < 0:
            return None
        return "%.0f%% + %.0f%s" % (self.coarse_level_pct(), \
                                    self.flowmeter.pumped_since_level_change(), \
                                    self.unit)

    def malfunction(self):
        return self.malfunction_bitmap

    def sensormap(self):
        smap = []
        for i, pct in enumerate(self.sensors):
            mask = 1 << i
            bit = self.latest_bitmap & mask
            bit = not bit # pull-up logic
            smap.append(bit and 1 or 0)
        return smap
