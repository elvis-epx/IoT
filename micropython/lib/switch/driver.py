# FIXME implement

class Direct4:
    def __init__(self):
        self.inputs = 4
        self.outputs = 4
        self.output_bits = 0
        self.output_mask = 0b1111

    def output_pin(self, pin, value):
        if value:
            self.output_bits |= (1 << pin)
        else:
            self.output_bits &= ~(1 << pin)
        self.output_bits &= self.output_mask

    def input(self):
        return 0
