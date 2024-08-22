from espnowtool.utils import *
import time
import os

# When mocking a peripheral, generate timestamp as a peripheral should do
# i.e. using last network-provided timestamp and add local clock advancement
def gen_timestamp_peripheral():
    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    net_ts, base = [int(n) for n in open(folder + "ts").read().split(" ")]
    t = int(time.time() * 1000) - base + net_ts
    return encode_timestamp(t)

# When mocking a peripheral, generate TID and save for later confirmation
def gen_tid_peripheral():
    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    tid = gen_tid()
    open(folder + "tx_tid", "w").write(b2s(tid))
    return tid

# When mocking a central, return latest TID sent by peripheral
def latest_received_tid():
    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    return s2b(open(folder + "rx_tid", "r").read())

# When mocking a central, generate a timestamp/confirm packet
def gen_ts(buf, args):
    if 'confirm' not in args:
        subtype = timestamp_subtype_default
    else:
        subtype = timestamp_subtype_confirm
        tid = args['confirm']
        if tid == "lasttid":
            tid = latest_received_tid()
    buf += bytearray([subtype])
    buf += gen_tid()
    timestamp = int(time.time() * 1000)
    buf += encode_timestamp(timestamp)
    if subtype == timestamp_subtype_confirm:
        buf += tid
    return buf

# When mocking a peripheral (for now) generate a data packet
def gen_data(buf, args):
    buf += gen_timestamp_peripheral()
    buf += gen_tid_peripheral()
    buf += args["payload"].replace("\\n", "\n").encode(args.get('encoding', 'utf-8'))
    return buf

pkttypes = {"ts": (type_timestamp, gen_ts, broadcast_mac),
            "data": (type_data, gen_data, other_mac) }

def tx_packet(psk, group, channel, pkttypename, args):
    pkttype, gen, dmac = pkttypes[pkttypename]
    buf = bytearray([version, pkttype])
    buf += group
    buf = gen(buf, args)
    buf = encrypt(psk, buf)
    buf += hmac(psk, buf)

    packet = bytes([channel]) + dmac + my_mac + buf

    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    f = "%.9f.rx" % time.time()
    open(folder + f, "wb").write(packet)
