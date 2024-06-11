class PZEM:
    def __init__(self, uart, addr=0xF8):
        pass

    def check_addr_start(self):
        self.read_addr_start()

    def set_addr_start(self, addr):
        pass

    def read_addr_start(self):
        pass

    def read_energy_start(self):
        pass

    def reset_energy_start(self):
        pass

    def complete_trans(self):
        return True

    def get_data(self):
        return {"V": 222.1,
                "A": 4.8,
                "W": 0.0,
                "Wh": 150,
                "Hz": 60.0,
                "pf": 0.7}
