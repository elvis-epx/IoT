from epx.loop import Task, SECONDS, reboot
import machine, onewire, ds18x20, binascii

class Sensor:
    def __init__(self, mqttpubadd, mqttpubclass):
        self.mqttpubadd = mqttpubadd
        self.mqttpubclass = mqttpubclass
        self.roms = {}
        self._malfunction = 0
        self.schedule_restart()

        self.impl = ds18x20.DS18X20(onewire.OneWire(14))
        Task(True, "sensor_scan", self.scan, 30 * SECONDS)

    def schedule_restart(self):
        if not self.malfunction_restart:
            self.malfunction_restart = Task(False, "sensor_fail_reset", self.restart, 15 * MINUTES)

    def cancel_restart(self):
        if self.malfunction_restart:
            self.malfunction_restart.cancel()
            self.malfunction_restart = None

    def restart(self, _):
        loop.reboot("Unrecoverable sensor malfunction")

    def scan(self, tsk):
        roms = self.impl.scan()

        if not roms:
            self.malfunction_ = 1
            return

        tsk.cancel()
        self.cancel_restart()

        for rom in roms:
            name = binascii.hexlify(rom)
            print('Found device', name)
            self.roms[name] = {}
            self.roms['raw'] = rom
            self.roms['temp'] = None           
            self.roms['mqtt'] = self.mqttpubclass(self, name)
            self.mqttpubadd(self.roms['mqtt'])

        # TODO add/remove sensors as we go, not only once?

        Task(True, "sensor_eval", self.eval, 30 * SECONDS)

    def eval(self, _):
        try:
            self.impl.convert_temp()
            Task(False, "sensor_eval2", self.eval_in, 1 * SECONDS)
        except onewire.OneWireError:
            self.malfunction_ = 2
            print("OneWireError in convert_temp")
            self.schedule_restart()

    def eval_in(self, _):
        malfunction = 1
        success = False

        for name in self.roms.keys():
            t = None
            try:
                t = ds_sensor.read_temp(self.roms[name]['raw'])
                success = True
                print("read_temp", name, t)
            except onewire.OneWireError:
                malfunction *= 3 # factor the malfunction code to count how many errors of this type
                self.schedule_restart()
                print("OneWireError in read_temp", name)
            except Exception:
                # CRC error
                malfunction *= 5
                self.schedule_restart()
                print("Exception in read_temp", name)
            self.roms[addr]['temp'] = t

        # TODO handle partial success more thoroughly e.g. resetting after some time, or rescan?

        if success:
            # At least one reading was successful
            self.malfunction_ = 0
            self.cancel_restart()
            return

        self.malfunction_ = malfunction
            
    def temperature(self, addr):
        if addr not in self.roms:
            return None
        return self.roms[addr]['temp']

    def malfunction(self):
        return self._malfunction
