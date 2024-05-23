from epx.loop import Task, SECONDS, MINUTES, Shortcronometer
from switch.service import ManualProgPub, ManualPub, ManualProgSub, ManualProgCompilationPub

# Handling of manual switches

class Manual:
    def __init__(self, nvram, mqtt, iodriver, switches, poll_time, debounce_time, longpress_time):
        self.nvram = nvram
        self.iodriver = iodriver
        self.switches = switches
        self.poll_time = poll_time
        self.debounce_time = debounce_time
        self.longpress_time = longpress_time

        self.handlers = {'P': self.eval_P, 'R': self.eval_R, 'T': self.eval_T}
        self.program_string = ""
        self.program_compilation_msg = ""

        n = self.iodriver.inputs
        self.input_current = [-1 for _ in range(0, n)]
        self.input_next = [-1 for _ in range(0, n)]
        self.debounce_crono = [None for _ in range(0, n)]
        self.longpress_task = [None for _ in range(0, n)]
        self.input_pub = [ mqtt.pub(ManualPub(self, "%d" % n, n)) for n in range(0, n) ]
        self.input_pub_value = [ "" for _ in range(0, n) ]
        self.program = {}

        self.pub = mqtt.pub(ManualProgPub(self))
        self.compilation_pub = mqtt.pub(ManualProgCompilationPub(self))
        self.sub = mqtt.sub(ManualProgSub(self))

        self.eval_task = Task(True, "manual_poll", self.eval, poll_time)

        self.program_in_nvram = self.nvram.get_str("program") or ""
        self.compile_program(self.program_in_nvram, True)

    # Gather input bits
    def eval(self, _):
        input_bits = self.iodriver.input()
        for n in range(0, self.iodriver.inputs):
            bit = (input_bits & (1 << n)) and 1 or 0
            self.eval_n(n, bit)

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
                    # still within debounce time
                    pass
                elif n not in self.program:
                    print("No program for manual %d" % n)
                    pass
                else:
                    # commit change
                    kind = self.program[n]['kind']
                    self.handlers[kind](n, self.input_current[n], self.input_next[n])
                    self.input_current[n] = self.input_next[n]
                    self.debounce_crono[n] = None
            else:
                # new bit pattern is flaky; quit
                self.debounce_crono[n] = None

    # Process manual switches that changed state

    # Pulse switch
    def eval_P(self, n, old, new):
        # Cancel any ongoing longpress timeout
        if self.longpress_task[n] is not None:
            self.longpress_task[n].cancel()
            self.longpress_task[n] = None

        if old == 0 and new == 1:
            # short pulse, rising edge
            self.run_program(n)
            self.input_pub_value[n] = "P"
            self.input_pub[n].forcepub()
            self.input_pub_value[n] = ""

            # schedule long-press timeout
            def cb(_):
                self.run_program_longpress(n)
                self.input_pub_value[n] = "L"
                self.input_pub[n].forcepub()
                self.input_pub_value[n] = ""

            self.longpress_task[n] = Task(False, "longpress", cb, self.longpress_time)

    # Regular manual switch, toggle mode
    def eval_T(self, n, old, new):
        # Remember that 'old' can be == -1 (undefined) at startup
        if old == 0 and new == 1:
            self.run_program(n)
            self.input_pub_value[n] = "T+"
            self.input_pub[n].forcepub()
            self.input_pub_value[n] = ""
        elif old == 1 and new == 0:
            self.run_program(n)
            self.input_pub_value[n] = "T-"
            self.input_pub[n].forcepub()
            self.input_pub_value[n] = ""

    # Regular manual switch, follow switch state
    def eval_R(self, n, old, new):
        if new == 1:
            self.run_program(n, phase=1)
            self.input_pub_value[n] = "R+"
            self.input_pub[n].forcepub()
            self.input_pub_value[n] = ""
        elif new == 0:
            self.run_program(n, phase=0)
            self.input_pub_value[n] = "R-"
            self.input_pub[n].forcepub()
            self.input_pub_value[n] = ""

    # Apply programs associated with manual
    # (generally, turning some lights on and others off)

    def run_program(self, n, phase=None):
        program = self.program[n]

        if phase is None:
            phase = self.detect_phase(program) + 1
        phase = phase % len(program['phases'])

        for sw, st in program['phases'][phase]['switches']:
            self.switches[sw].switch(st)

    def run_program_longpress(self, n):
        self.run_program(n, phase=0)

    def detect_phase(self, program):
        for i, phase in enumerate(program['phases']):
            for sw, exp_state in phase['switches']:
                actual_state = self.switches[sw].is_on()
                if exp_state != actual_state:
                    break
            else:
                return i
        return 0

    # Compile new program

    def compile_program(self, p, try_default):
        err = self.do_compile_program(p)
        if not err:
            self.program_compilation_msg = "Success"
        else:
            print(err)
            self.program_compilation_msg = err
            if try_default:
                p = self.default_program()
                err = self.do_compile_program(p)
                if err:
                    print(err)
                    self.program_compilation_msg = "Double fault"
                else:
                    self.program_compilation_msg = "Success"
        self.compilation_pub.forcepub()

    def do_compile_program(self, pstring):
        pstring = pstring.strip()

        print("Compiling program", pstring)
        programs = {}

        # manual record 1 ; manual record 2 ; ...
        # always has at least 1 element
        p = [s.strip() for s in pstring.strip().split(";")]

        for pms in p:
            if not pms:
                continue

            # manual nr. : program kind : phases
            print("\tCompiling manual", pms)

            pm = [s.strip() for s in pms.split(":")]
            if len(pm) != 3:
                return "Program manual unexp: " + pms

            manual, kind, sphases = pm

            try:
                manual = int(manual) % len(self.input_current)
            except ValueError:
                return "Program manual# unexp: " + pms

            if kind not in self.handlers:
                return "Program kind unexp: " + pms

            print("\tManual %d kind %s" % (manual, kind))

            program = {}
            program['kind'] = kind
            program['phases'] = []

            # Phases separated by /
            # There should be at least 2

            phases = [s.strip() for s in sphases.split("/")]
            # always has at least 1 element
            # we admit this so there can be manual switches that only do one thing
            # e.g. only turn lights on, or only turn lights off

            # example of 1 manual controlling 1 light, two phases: +1 / -1
            # example of 1 manual controlling 2 lights, four phases: -1,-2 / +1,+2 / +1,-2 / -1,+2

            for phase in phases:
                if not phase:
                    return "Phase empty"
                print("\t\tPhase", phase)
                # Parse switch(es) of every given phase
                switches = [s.strip() for s in phase.split(",")]

                switch_list = []
                phase_dict = {'switches': switch_list}
                program['phases'].append(phase_dict)

                for switch in switches:
                    # Switch is +n or -n where "n" is the switch number
                    if len(switch) < 2:
                        return "Switch len unexp: " + phase

                    newstate = switch[0]
                    switch = switch[1:]

                    if newstate not in ('+', '-'):
                        return "Switch sign unexp: " + phase
                    newstate = newstate == '+' and 1 or 0

                    try:
                        switch = int(switch) % len(self.switches)
                    except ValueError:
                        return "Phase switch# unexp: " + phase

                    print("\t\t\tSwitch %d: %s" % (switch, newstate and "On" or "Off"))
                    switch_list.append((switch, newstate))

            programs[manual] = program

        if not programs:
            return "Program is nil"

        # New program parsed and accepted as good; commit

        self.program = {}
        for manual, program in programs.items():
            self.program[manual] = program

        if pstring != self.program_in_nvram:
            self.nvram.set_str("program", pstring)
            self.program_in_nvram = pstring

        self.program_string = pstring
        self.pub.forcepub()

        return ""

    # If there is no program, tie every manual[n] to switch[n]

    def default_program(self):
        p = ""
        for n in range(0, len(self.input_current)):
            switch = n % len(self.switches)
            p += "%d:P:-%d/+%d; " % (n, switch, switch)
        return p

    def program_str(self):
        return self.program_string

    def program_compilation_status(self):
        return self.program_compilation_msg

    def manual_event(self, n):
        return self.input_pub_value[n]

# Program "language"
# a:X:+b,-c/-b,+c;
# a = manual switch input pin (0..n)
# X = program type. Currently, the following types are implemented:
#     P: pulsating switch
#     T: regular switch that changes the state when toggled
#     R: regular on/off switch
# b,c = relay output pins (0..n)
# Programs separated by semicolon ;
# Phases of a program separated by slash /
# Relays affected in each phase separated by comma ,
#
# Example:
# 0:P:-0/+0; 1:P:-1,-2/+1,+2/+1,-2/-1,+2; 2:T:-3/+3
#
# Manual 0 is a pulsating switch that controls relay 0
# Manual 1, pulsating, controls relays 1 and 2, in four phases
#          (off+off, on+on, on+off, off+on)
# Manual 2, regular switch used as toggler, controls relay 3
# Manual 3 (if exists) unused
#
# In P type, long press goes to 1st phase, so it is best the first phase
# turns all lights off.
# The T type is very similar to the P type, except that it changes phase
# when toggled instead of pulsed. T does not have the concept of long press.
# An R program should have exactly two phases, "off" and "on" to work as
# expected by users. 
# For R switches, the respective lights may still be overridden by MQTT
# commands, but if the module resets, the state of the manual switch
# supersedes the last known state in NVRAM.
