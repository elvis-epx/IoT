import machine
from third.pzem import PZEM
from epx.loop import Task, SECONDS, MINUTES, StateMachine, Shortcronometer

if hasattr(machine, 'TEST_ENV'):
    READ_EVERY = 1 * SECONDS
    ENERGY_PUB_TIMEOUT = 60 * SECONDS
    STARTUP_TIMEOUT = 1 * SECONDS
    RESPONSE_TIMEOUT = 1 * SECONDS
    FAILURE_TIMEOUT = 20 * SECONDS
else: # pragma: no cover
    READ_EVERY = 1 * SECONDS
    ENERGY_PUB_TIMEOUT = 60 * MINUTES
    STARTUP_TIMEOUT = 20 * SECONDS
    RESPONSE_TIMEOUT = 1 * SECONDS
    FAILURE_TIMEOUT = 10 * MINUTES

class Sensor:
    def __init__(self):
        self.data = {"V": None, "A": None, "W": None, "Wh": None, "pf": None, "t": None, "Malfunction": 0}
        self.energy_observer = None
        self.energy_timer = None
        self.uart = machine.UART(2, baudrate=9600)
        sm = self.sm = StateMachine("sensor")

        sm.add_state("start", self.on_start)
        sm.add_state("startcompletion", self.on_startcompletion)
        sm.add_state("resetenergy", self.on_resetenergy)
        sm.add_state("resetenergycompletion", self.on_resetenergycompletion)
        sm.add_state("read", self.on_read)
        sm.add_state("readcompletion", self.on_readcompletion)
        sm.add_state("idle", self.on_idle)
        sm.add_state("pubenergy", self.on_pubenergy)
        sm.add_state("failure", self.on_failure)

        sm.add_transition("initial", "start")
        sm.add_transition("start", "startcompletion")
        sm.add_transition("startcompletion", "failure")
        sm.add_transition("startcompletion", "resetenergy")
        sm.add_transition("resetenergy", "resetenergycompletion")
        sm.add_transition("resetenergycompletion", "failure")
        sm.add_transition("resetenergycompletion", "read")
        sm.add_transition("read", "readcompletion")
        sm.add_transition("readcompletion", "failure")
        sm.add_transition("readcompletion", "idle")
        sm.add_transition("idle", "read")
        sm.add_transition("idle", "pubenergy")
        sm.add_transition("pubenergy", "resetenergy")
        sm.add_transition("failure", "start")

        self.sm.schedule_trans("start", STARTUP_TIMEOUT)

    def register_energy_observer(self, observer):
        self.energy_observer = observer

    def on_start(self):
        self.impl = PZEM(uart=self.uart)
        self.impl.check_addr_start()
        self.sm.schedule_trans("startcompletion", RESPONSE_TIMEOUT)

    def on_startcompletion(self):
        if not self.impl.complete_trans():
            print("Error while starting pzem")
            self.data['Malfunction'] = 1
            self.sm.schedule_trans_now("failure")
            return

        self.sm.schedule_trans_now("resetenergy")

    def on_resetenergy(self):
        self.impl.reset_energy_start()
        self.sm.schedule_trans("resetenergycompletion", RESPONSE_TIMEOUT)

    def on_resetenergycompletion(self):
        if not self.impl.complete_trans():
            print("Error while resetting energy") 
            self.data['Malfunction'] = 2
            self.sm.schedule_trans_now("failure")
            return

        self.energy_timer = Shortcronometer()
        self.sm.schedule_trans_now("read")

    def on_read(self):
        self.impl.read_energy_start()
        self.sm.schedule_trans("readcompletion", RESPONSE_TIMEOUT)

    def on_readcompletion(self):
        if not self.impl.complete_trans():
            print("Error while reading energy") 
            self.data['Malfunction'] = 4 
            self.sm.schedule_trans_now("failure")
            return

        self.data['Malfunction'] = 0
        self.data.update(self.impl.get_data())
        self.data['t'] = int(self.energy_timer.elapsed() / 1000)
        self.sm.schedule_trans_now("idle")

    def on_idle(self):
        if self.energy_timer.elapsed() > ENERGY_PUB_TIMEOUT:
            self.sm.schedule_trans_now("pubenergy")
            return
        self.sm.schedule_trans("read", READ_EVERY)

    def on_pubenergy(self):
        if self.energy_observer:
            self.energy_observer.please_publish()
        self.sm.schedule_trans_now("resetenergy")

    def on_failure(self):
        self.sm.schedule_trans("start", FAILURE_TIMEOUT)

    def voltage(self):
        if self.data['Malfunction']:
            return None
        return self.data['V']

    def current(self):
        if self.data['Malfunction']:
            return None
        return self.data['A']

    def power(self):
        if self.data['Malfunction']:
            return None
        return self.data['W']

    def powerfactor(self):
        if self.data['Malfunction']:
            return None
        return self.data['pf']

    def energy(self):
        if self.data['Malfunction']:
            return None
        elif self.data['Wh'] is None:
            return None
        return self.data['Wh'] + 0.0

    def malfunction(self):
        return self.data['Malfunction']

    def jsonish(self):
        return str(self.data) + "\r\n"
