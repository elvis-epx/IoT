import machine
from third.pzem import PZEM
from epx.loop import Task, SECONDS, MINUTES, StateMachine, Shortcronometer

if hasattr(machine, 'TEST_ENV'):
    READ_EVERY = 1 * SECONDS
    PUB_TIMEOUT = 60 * SECONDS
    STARTUP_TIMEOUT = 1 * SECONDS
    RESPONSE_TIMEOUT = 1 * SECONDS
    FAILURE_TIMEOUT = 20 * SECONDS
else: # pragma: no cover
    READ_EVERY = 1 * SECONDS
    PUB_TIMEOUT = 60 * SECONDS
    STARTUP_TIMEOUT = 20 * SECONDS
    RESPONSE_TIMEOUT = 1 * SECONDS
    FAILURE_TIMEOUT = 10 * MINUTES

agg_data_clean = {"Vavg": 0.0, "Vmin": 999999.9, "Vmax": 0.0, \
                  "Aavg": 0.0, "Amax": 0.0, \
                  "Wavg": 0.0, \
                  "pfavg": 0.0, \
                  "n": 0}

class Sensor:
    def __init__(self):
        self.visible_data = {"V": None, "Vavg": None, "Vmin": None, "Vmax": None, \
                        "A": None, "Aavg": None, "Amax": None, \
                        "W": None, "Wavg": None, \
                        "pf": None, "pfavg": None, \
                        "Malfunction": 0, "t": None, "n": None}
        self.agg_data = None
        self.pub_list = []
        self.pub_timer = None
        self.uart = machine.UART(2, baudrate=9600)
        sm = self.sm = StateMachine("sensor")

        sm.add_state("start", self.on_start)
        sm.add_state("startcompletion", self.on_startcompletion)
        sm.add_state("startaggregation", self.on_startaggregation)
        sm.add_state("read", self.on_read)
        sm.add_state("readcompletion", self.on_readcompletion)
        sm.add_state("idle", self.on_idle)
        sm.add_state("pubaggregate", self.on_pubaggregate)
        sm.add_state("failure", self.on_failure)

        sm.add_transition("initial", "start")
        sm.add_transition("start", "startcompletion")
        sm.add_transition("startcompletion", "failure")
        sm.add_transition("startcompletion", "startaggregation")
        sm.add_transition("startaggregation", "read")
        sm.add_transition("read", "readcompletion")
        sm.add_transition("readcompletion", "failure")
        sm.add_transition("readcompletion", "idle")
        sm.add_transition("idle", "read")
        sm.add_transition("idle", "pubaggregate")
        sm.add_transition("pubaggregate", "startaggregation")
        sm.add_transition("failure", "start")

        self.sm.schedule_trans("start", STARTUP_TIMEOUT)

    def pub_add(self, pub):
        if pub not in self.pub_list:
            self.pub_list.append(pub)

    def on_start(self):
        self.impl = PZEM(uart=self.uart)
        self.impl.check_addr_start()
        self.sm.schedule_trans("startcompletion", RESPONSE_TIMEOUT)

    def on_startcompletion(self):
        if not self.impl.complete_trans():
            print("Error while starting pzem")
            self.visible_data['Malfunction'] = 1
            self.sm.schedule_trans_now("failure")
            return
        self.sm.schedule_trans_now("startaggregation")

    def on_startaggregation(self):
        self.agg_data = agg_data_clean.copy()
        self.pub_timer = Shortcronometer()
        self.sm.schedule_trans_now("read")

    def on_read(self):
        self.impl.read_energy_start()
        self.sm.schedule_trans("readcompletion", RESPONSE_TIMEOUT)

    def on_readcompletion(self):
        if not self.impl.complete_trans():
            print("Error while reading energy") 
            self.visible_data['Malfunction'] = 4 
            self.sm.schedule_trans_now("failure")
            return

        self.visible_data['Malfunction'] = 0
        sensor_data = self.impl.get_data()

        self.visible_data.update(sensor_data)
        self.visible_data['t'] = int(self.pub_timer.elapsed() / 1000)
        self.update_aggregates(sensor_data)

        self.sm.schedule_trans_now("idle")

    def update_aggregates(self, sensor_data):
        w = self.agg_data["n"]
        for k in ("V", "A", "W", "pf"):
            if (k + "avg") in self.agg_data:
                self.agg_data[k + "avg"] = (self.agg_data[k + "avg"] * w + sensor_data[k]) / (w + 1.0)
            if (k + "min") in self.agg_data:
                self.agg_data[k + "min"] = min(self.agg_data[k + "min"], sensor_data[k])
            if (k + "max") in self.agg_data:
               self.agg_data[k + "max"] = max(self.agg_data[k + "max"], sensor_data[k])
        self.agg_data["n"] += 1

    def on_idle(self):
        if self.pub_timer.elapsed() > PUB_TIMEOUT:
            self.sm.schedule_trans_now("pubaggregate")
            return
        self.sm.schedule_trans("read", READ_EVERY)

    def on_pubaggregate(self):
        if self.agg_data["n"] > 0:
            self.visible_data.update(self.agg_data)
            for pub in self.pub_list:
                pub.forcepub()
        self.sm.schedule_trans_now("startaggregation")

    def on_failure(self):
        self.sm.schedule_trans("start", FAILURE_TIMEOUT)

    def get_data(self, k):
        if self.visible_data['Malfunction']:
            return None # pragma: no cover
        return self.visible_data[k]

    def malfunction(self):
        return self.visible_data['Malfunction']

    def jsonish(self):
        return str(self.visible_data) + "\r\n"
