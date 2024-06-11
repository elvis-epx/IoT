from pzem import PZEM
import machine
import time

uart = machine.UART(2, baudrate=9600)
dev = PZEM(uart=uart)
dev.check_addr_start()
time.sleep(1)
if not dev.complete_trans():
    raise Exception("Could not check addr")

while True:
    dev.reset_energy_start()
    time.sleep(1)
    if not dev.complete_trans():
        print("Erro ao resetar energia")

    for _ in range(0, 60):
        dev.read_energy_start()
        time.sleep(1)
        if dev.complete_trans():
            print(dev.get_data())
        else:
            print("Erro")
