from time import sleep_ms
from machine import Pin, SoftSPI, reset
from sx127x import SX127x

# TTGO-LoRa32 v1.0 pinout. Other versions have different pinouts.
PIN_ID_FOR_LORA_RESET = 14
PIN_ID_FOR_LORA_SS = 18
PIN_ID_SCK = 5
PIN_ID_MOSI = 27
PIN_ID_MISO = 19
PIN_ID_FOR_LORA_DIO0 = 26
PIN_ID_FOR_LORA_DIO1 = None
PIN_ID_FOR_LORA_DIO2 = None
PIN_ID_FOR_LORA_DIO3 = None
PIN_ID_FOR_LORA_DIO4 = None
PIN_ID_FOR_LORA_DIO5 = None


class TTGOLoRa:
    class Mock:
        pass

    def __init__(self):
        pin_id_reset = PIN_ID_FOR_LORA_RESET
        self.pin_reset = self.prepare_pin(pin_id_reset)
        self.reset_pin(self.pin_reset)
        self.lora = self.add_transceiver(SX127x(name = 'LoRa',
                             parameters = {'frequency': 915E6, 'tx_power_level': 17, 'signal_bandwidth': 250E3,
                               'spreading_factor': 7, 'coding_rate': 5, 'preamble_length': 8,
                               'implicitHeader': False, 'sync_word': 0x12, 'enable_CRC': False}))

    def add_transceiver(self,
                        transceiver,
                        pin_id_ss = PIN_ID_FOR_LORA_SS,
                        pin_id_RxDone = PIN_ID_FOR_LORA_DIO0,
                        pin_id_RxTimeout = PIN_ID_FOR_LORA_DIO1,
                        pin_id_ValidHeader = PIN_ID_FOR_LORA_DIO2,
                        pin_id_CadDone = PIN_ID_FOR_LORA_DIO3,
                        pin_id_CadDetected = PIN_ID_FOR_LORA_DIO4,
                        pin_id_PayloadCrcError = PIN_ID_FOR_LORA_DIO5):

        transceiver.pin_ss = self.prepare_pin(pin_id_ss)
        transceiver.pin_RxDone = self.prepare_irq_pin(pin_id_RxDone)
        transceiver.pin_RxTimeout = self.prepare_irq_pin(pin_id_RxTimeout)
        transceiver.pin_ValidHeader = self.prepare_irq_pin(pin_id_ValidHeader)
        transceiver.pin_CadDone = self.prepare_irq_pin(pin_id_CadDone)
        transceiver.pin_CadDetected = self.prepare_irq_pin(pin_id_CadDetected)
        transceiver.pin_PayloadCrcError = self.prepare_irq_pin(pin_id_PayloadCrcError)

        self.spi = self.prepare_spi(self.get_spi())
        transceiver.transfer = self.spi.transfer

        transceiver.init()

        return transceiver

    def reset_pin(self, pin):
        pin.low()
        sleep_ms(50)
        pin.high()
        sleep_ms(50)

    def prepare_pin(self, pin_id, in_out = Pin.OUT):
        if pin_id is not None:
            pin = Pin(pin_id, in_out)
            new_pin = TTGOLoRa.Mock()
            new_pin.pin_id = pin_id
            new_pin.value = pin.value

            if in_out == Pin.OUT:
                new_pin.low = lambda : pin.value(0)
                new_pin.high = lambda : pin.value(1)
            else:
                new_pin.irq = pin.irq

            return new_pin


    def prepare_irq_pin(self, pin_id):
        pin = self.prepare_pin(pin_id, Pin.IN)
        if pin:
            pin.set_handler_for_irq_on_rising_edge = lambda handler: pin.irq(handler = handler, trigger = Pin.IRQ_RISING)
            pin.detach_irq = lambda : pin.irq(handler = None, trigger = 0)
            return pin


    def get_spi(self):
        spi = None

        try:
            spi = SoftSPI(baudrate = 10000000, polarity = 0, phase = 0, bits = 8, firstbit = SoftSPI.MSB,
                      sck = Pin(PIN_ID_SCK, Pin.OUT, Pin.PULL_DOWN),
                      mosi = Pin(PIN_ID_MOSI, Pin.OUT, Pin.PULL_UP),
                      miso = Pin(PIN_ID_MISO, Pin.IN, Pin.PULL_UP))
            #spi.init()

        except Exception as e:
            print(e)
            if spi:
                spi.deinit()
                spi = None
            reset()  # in case SPI is already in use, need to reset.

        return spi


    def prepare_spi(self, spi):

        if spi:
            new_spi = TTGOLoRa.Mock()

            def transfer(pin_ss, address, value = 0x00):
                response = bytearray(1)

                pin_ss.low()

                spi.write(bytes([address]))
                spi.write_readinto(bytes([value]), response)

                pin_ss.high()

                return response

            new_spi.transfer = transfer
            new_spi.close = spi.deinit
            return new_spi
