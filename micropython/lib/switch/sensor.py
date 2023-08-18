from epx.loop import Task, SECONDS, MINUTES, Shortcronometer
from switch.service import ManualProgPub, ManualPub, ManualProgSub

# Handling of manual switches

class Manual:
    def __init__(self, mqtt, iodriver, switches, poll_time, debounce_time):
        self.iodriver = iodriver
        self.switches = switches
        self.poll_time = poll_time
        self.debounce_time = debounce_time

        self.program_string = ""

        n = self.iodriver.inputs
        self.input_current = [-1 for _ in range(0, n)]
        self.input_next = [-1 for _ in range(0, n)]
        self.debounce_crono = [None for _ in range(0, n)]
        self.input_pub = [ mqtt.pub(ManualPub(self, "%d" % n, n)) for n in range(0, n) ]
        self.input_pub_value = [ "" for _ in range(0, n) ]
        self.program = [lambda: None for _ in range(0, n)]

        self.pub = mqtt.pub(ManualProgPub(self))
        self.sub = mqtt.sub(ManualProgSub(self))

        self.eval_task = Task(True, "manual_poll", self.eval, poll_time)

        # FIXME NVRAM x prog, program compiling, etc:
        self.compile_program("")

    # Gather input bits
    def eval(self, _):
        input_bits = self.iodriver.input()
        for n in range(0, self.iodriver.inputs):
            self.eval_n(n, (input_bits & (1 << n)) and 1 or 0)

    # Per-manual switch processing
    def eval_n(self, n, bit):
        if self.debounce_crono[n] is None:
            # initial state
            if self.input_current[n] == bit:
                # no change
                pass
            else:
                # detected change, start debouncing time
                self.input_next[n] = bit
                self.debounce_crono[n] = Shortcronometer()
        else:
            # debouncing time
            if bit == self.input_next[n]:
                # new bit pattern is holding
                if self.debounce_crono[n].elapsed() < self.debounce_time:
                    # still in debounce time
                    pass
                else:
                    # commit change
                    self.eval_in(n, self.input_current[n], self.input_next[n])
                    self.input_current[n] = self.input_next[n]
                    self.debounce_crono[n] = None
            else:
                # new bit pattern is flaky; quit
                self.debounce_crono[n] = None

    # Process manual switches that changed state

    def eval_in(self, n, old, new):
        if old == 0 and new == 1:
            # Currently, only implementation is the pulse switch
            print("manual %d pulsed" % n)
            self.input_pub_value[n] = "P"
            self.input_pub[n].force_pub()
            self.input_pub_value[n] = ""
            self.program[n]()

    # Compile new program

    def compile_program(self, p):
        # FIXME TODO
        self.program_string = p
        pass

    def program_str(self):
        return self.program_string

    def manual_event(self, n):
        return self.input_pub_value[n]


    # FIXME TODO detect current "carousel" stage based on current stage of switches
