from epx.loop import Task, SECONDS, MINUTES, Shortcronometer
from switch.service import ManualProgPub, ManualPub, ManualProgSub, ManualProgCompilationPub

# Handling of manual switches

class Manual:
    def __init__(self, nvram, mqtt, iodriver, switches, poll_time, debounce_time):
        self.nvram = nvram
        self.iodriver = iodriver
        self.switches = switches
        self.poll_time = poll_time
        self.debounce_time = debounce_time

        self.program_string = ""
        self.program_compilation_msg = ""

        n = self.iodriver.inputs
        self.input_current = [-1 for _ in range(0, n)]
        self.input_next = [-1 for _ in range(0, n)]
        self.debounce_crono = [None for _ in range(0, n)]
        self.input_pub = [ mqtt.pub(ManualPub(self, "%d" % n, n)) for n in range(0, n) ]
        self.input_pub_value = [ "" for _ in range(0, n) ]
        self.program = [None for _ in range(0, n)]

        self.pub = mqtt.pub(ManualProgPub(self))
        self.compilation_pub = mqtt.pub(ManualProgCompilationPub(self))
        self.sub = mqtt.sub(ManualProgSub(self))

        self.eval_task = Task(True, "manual_poll", self.eval, poll_time)

        self.compile_program(self.nvram.get_str("program") or "", True)

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
            self.run_program(n)

    # Apply program associated with manual
    # (generally, turning some lights on and others off)

    def run_program(self, n):
        program = self.program[n]
        if not program:
            print("No program for manual %d" % n)
            return
        phase = self.detect_phase(program)
        new_phase = (phase + 1) % len(program['phases'])
        for sw, st in program['phases'][phase]['switches']:
            self.switches[sw].switch(st)

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
                    print("Success")
                    self.program_compilation_msg = "Success"
        self.compilation_pub.forcepub()

    def do_compile_program(self, pstring):
        pstring = pstring.strip()
        if not pstring:
            return "Program is nil"

        print("Compiling program", pstring)
        programs = {}

        # manual record 1 ; manual record 2 ; ...

        p = [s.strip() for s in pstring.strip().split(";")]

        for pm in p:
            if not pm:
                continue

            # manual nr. : program kind : phases
            print("\tCompiling manual", pm)

            pm = [s.strip() for s in pm.split(":")]
            if len(pm) != 3:
                return "Program manual unexp: " + pm

            manual, kind, phases = pm

            try:
                manual = int(manual) % len(self.program)
            except ValueError:
                return "Program manual# unexp: " + pm

            if kind not in ('P', ):
                return "Program kind unexp: " + pm

            print("\tManual %d kind %s" % (manual, kind))

            program = {}
            program['kind'] = kind
            program['phases'] = []

            # Phases separated by /
            # There should be at least 2

            phases = [s.strip() for s in phases.split("/")]

            if len(phases) < 2:
                return "Phase list len unexp: " + phases

            # example of 1 manual controlling 1 light, two phases: +1 / -1
            # example of 1 manual controlling 2 lights, four phases: -1,-2 / +1,+2 / +1,-2 / -1,+2

            for phase in phases:
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

        # New program parsed and accepted as good; commit

        for manual, program in programs.items():
            self.program[manual] = program

        self.program_string = pstring
        self.nvram.set_str("program", self.program_string)
        self.pub.forcepub()

        return ""

    # If there is no program, tie every manual[n] to switch[n]

    def default_program(self):
        p = ""
        for n in range(0, len(self.program)):
            switch = n % len(self.switches)
            p += "%d:P:+%d/-%d; " % (n, switch, switch)
        return p

    def program_str(self):
        return self.program_string

    def program_compilation_status(self):
        return self.program_compilation_msg

    def manual_event(self, n):
        return self.input_pub_value[n]
