from time import ticks_ms
import random
from reedsolo import RSCodec
import gc

rs = RSCodec(4)

msgCount = 0
INTERVAL_BASE = 5000
INTERVAL_FUDGE = 5000

display = None

received = []

def duplexCallback(lora, pdisplay):
    global display
    display = pdisplay
    print("LoRa Duplex with callback")
    lora.on_receive(on_receive)  # register the receive callback
    do_loop(lora)


def do_loop(lora):
    global msgCount

    lastSendTime = 0
    interval = 0
    last_code_recv = "xxxxx"

    while True:
        if received:
            payload, rssi = received[0]
            received.pop(0)
            print("Received message len {} RSSI {}".format(len(payload), rssi))

            try:
                bmsg, _, errors = rs.decode(payload)
                errors = len(errors)
            except:
                errors = 999

            if errors >= 999:
                msg = "Corrupted"
            else:
                try:
                    msg = bmsg.decode()
                    last_code_recv = msg[-5:]
                except:
                    msg = "Invalid"

            print("    Payload:", msg)

            display.fill(0)
            display.text("Recv {} {}".format(rssi, len(payload)), 0, 0, 1)
            display.text(msg[-15:], 0, 12, 1)
            display.text("errors {}".format(errors), 0, 24, 1)
            display.show()

            gc.collect()
            continue

        now = ticks_ms()

        if (now - lastSendTime > interval):
            lastSendTime = now                                      # timestamp the message
            interval = int(INTERVAL_BASE + random.random() * INTERVAL_FUDGE)

            smessage = ("r%s t%05d" % (last_code_recv, msgCount)).encode()
            message = rs.encode(smessage)
            t0 = ticks_ms()
            sendMessage(lora, message)                              # send message
            t1 = ticks_ms()
            print("Message sent in %d ms: " % (t1 - t0), smessage)

            display.fill(0)
            display.text("Sent {} ms".format(t1 - t0), 0, 0, 1)
            display.text(smessage[-15:], 0, 12, 1)
            display.show()

            msgCount += 1

            lora.receive()                                          # go into receive mode


def sendMessage(lora, outgoing):
    lora.send(outgoing)


def on_receive(lora, payload):
    rssi = lora.packetRssi()
    received.append((payload, rssi))
