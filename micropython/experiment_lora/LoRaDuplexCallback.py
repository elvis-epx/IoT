from time import ticks_ms
import random

msgCount = 0            # count of outgoing messages
INTERVAL = 5000         # interval between sends
INTERVAL_BASE = 5000    # interval between sends base

display = None

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

    while True:
        now = ticks_ms()

        if (now - lastSendTime > interval):
            lastSendTime = now                                      # timestamp the message
            interval = int(INTERVAL_BASE + random.random() * INTERVAL)

            message = "abracadabra %06d" % msgCount
            t0 = ticks_ms()
            sendMessage(lora, message)                              # send message
            t1 = ticks_ms()
            print("Message sent in %d ms" % (t1 - t0))

            display.fill(0)
            display.text("Sent {} ms".format(t1 - t0), 0, 0, 1)
            display.show()

            msgCount += 1

            lora.receive()                                          # go into receive mode


def sendMessage(lora, outgoing):
    lora.send(outgoing.encode())


def on_receive(lora, payload):
    rssi = lora.packetRssi()
    print("*** Received message len {} RSSI {}".format(len(payload), rssi))
    display.fill(0)
    display.text("Recv RSSI {}".format(rssi), 0, 0, 1)
    display.text("size {}".format(len(payload)), 0, 12, 1)
    display.show()
