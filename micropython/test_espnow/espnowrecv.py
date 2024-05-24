import network, espnow, time

sta = network.WLAN(network.STA_IF); sta.active(False)
sta.active(True)
sta.config(channel=6)

e = espnow.ESPNow()
e.active(True)

while True:
    if e.any():
        print(e.recv())
