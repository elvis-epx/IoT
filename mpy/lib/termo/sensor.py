from epx.loop import Task, SECONDS, MINUTES, reboot
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
            self.roms[name]['temp'] = None           
            self.roms[name]['mqtt'] = self.mqttpubclass(self, name)
            self.mqttpubadd(self.roms[name]['mqtt'])

        # TODO add/remove sensors as we go, not only once?

        task = Task(True, "sensor_eval", self.eval, 10 * SECONDS)
        task.advance()

    def eval(self, _):
        try:
            self.impl.convert_temp()
            Task(False, "sensor_eval2", self.eval_in, 1 * SECONDS)
        except onewire.OneWireError:
            self._malfunction = 2
            print("OneWireError in convert_temp")
            self.schedule_restart()

    def eval_in(self, _):
        malfunction = 1
        success = False

        for name in self.roms.keys():
            t = None
            try:
                t = self.impl.read_temp(self.roms[name]['raw'])
                success = True
                print("read_temp", name, t)
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
            self.roms[name]['temp'] = t

        # TODO handle partial success more thoroughly e.g. resetting after some time, or rescan?

        if success:
            # At least one reading was successful
            self._malfunction = 0
            self.cancel_restart()
            return

        self._malfunction = malfunction
            
    def temperature(self, name):
        if name not in self.roms:
            return None
        return self.roms[name]['temp']

    def malfunction(self):
        return self._malfunction
