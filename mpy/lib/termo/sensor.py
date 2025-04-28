from epx.loop import Task, SECONDS, MINUTES, reboot, Shortcronometer
import machine, onewire, ds18x20, binascii

class Sensor:
    def __init__(self, mqttpubadd, mqttpubclass):
        self.mqttpubadd = mqttpubadd
        self.mqttpubclass = mqttpubclass
        self.roms = {}
        self._malfunction = None
        self.malfunction_restart = None
        self.schedule_restart()

        self.impl = ds18x20.DS18X20(onewire.OneWire(machine.Pin(14)))
        Task(True, "sensor_scan", self.scan, 30 * SECONDS)

    def schedule_restart(self):
        if not self.malfunction_restart:
            self.malfunction_restart = Task(False, "sensor_fail_reset", self.restart, 15 * MINUTES)

    def cancel_restart(self):
        if self.malfunction_restart:
            self.malfunction_restart.cancel()
            self.malfunction_restart = None

    def restart(self, _):
        reboot("Unrecoverable sensor malfunction")

    def scan(self, tsk):
        roms = self.impl.scan()

        if not roms:
            print('No devices found in scan')
            self._malfunction = 1
            return

        tsk.cancel()
        self.cancel_restart()

        for rom in roms:
            name = binascii.hexlify(rom).decode('ascii')
            print('Found device', name)
            self.roms[name] = {}
            self.roms[name]['raw'] = rom
            self.roms[name]['dt'] = Shortcronometer()
            self.roms[name]['z'] = None
            self.roms[name]['x'] = None  # Use first measurement as initial estimation
            self.roms[name]['R'] = 0.5 ** 2 # in ºC squared (sensor accuracy)
            self.roms[name]['P'] = 10.0 ** 2 # in ºC squared (accuracy of initial estimation)
            # variance of estimation i.e. likelyhood of current temperature to stay the same
            self.roms[name]['Q/dt'] = 0.25 ** 2 / 60000 # in (ºC/min) squared and converted to ms
            self.roms[name]['mqtt'] = self.mqttpubclass(self, name)
            self.mqttpubadd(self.roms[name]['mqtt'])

        # TODO add/remove sensors as we go, not only once?

        task = Task(False, "sensor_eval", self.eval, 4 * SECONDS) # actually 5s due to convert_temp() step
        task.advance()

    def eval(self, eval_task):
        try:
            self.impl.convert_temp()
            def eval_in(_):
                self.eval_in(eval_task)
            Task(False, "sensor_eval2", eval_in, 1 * SECONDS)
        except onewire.OneWireError:
            self._malfunction = 2
            print("OneWireError in convert_temp")
            self.schedule_restart()

    def eval_in(self, eval_task):
        malfunction = 1
        success = False

        for name in self.roms.keys():
            t = None
            try:
                t = self.impl.read_temp(self.roms[name]['raw'])
                success = True
            except onewire.OneWireError:
                malfunction *= 3 # factor the malfunction code to count how many errors of this type
                self.schedule_restart()
                print("OneWireError in read_temp", name)
            except Exception as e:
                # CRC error
                malfunction *= 5
                self.schedule_restart()
                print("Exception in read_temp", name)
                print(e)

            if t is not None:
                self.roms[name]['z'] = t
                self.kalman(name, self.roms[name])

        # TODO handle partial success more thoroughly e.g. resetting after some time, or rescan?

        if success:
            # At least one reading was successful
            self._malfunction = 0
            self.cancel_restart()
        else:
            self._malfunction = malfunction

        eval_task.restart()

    def temperature(self, name):
        if name not in self.roms:
            return None
        return self.roms[name]['x']

    def malfunction(self):
        return self._malfunction

    def kalman(self, name, s):
        if s['x'] is None:
            # set initial estimation = first sensor reading
            s['x'] = s['z']

        dt = s['dt'].elapsed()
        s['dt'] = Shortcronometer()

        Pant = s['P']
        Q = s['Q/dt'] * dt
        Pm = Pant + Q
        K = Pm / (Pm + s['R'])
        s['x'] = K * s['z'] + (1 - K) * s['x']
        s['P'] = (1 - K) * Pm

        print("read_temp", name, "z", "%.4f" % s['z'], "x", "%.4f" % s['x'], "dt", dt, "P", "%.5f" % Pant, "Q", "%.5f" % Q, "Pm", "%.5f" % Pm, "K", "%.5f" % K, "P+", "%.5f" % s['P'])
