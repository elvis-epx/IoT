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

# When mocking a center, generate TID and save for later usage
def gen_tid_central(repeat_last):
    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    if repeat_last:
        tid = s2b(open(folder + "txc_tid").read())
    else:
        tid = gen_tid()
        open(folder + "txc_tid", "w").write(b2s(tid))
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
    buf += gen_tid_central('sametid' in args)
    timestamp = int(time.time() * 1000)
    buf += encode_timestamp(timestamp)
    if subtype == timestamp_subtype_confirm:
        buf += tid
        if 'badlen3' in args:
            buf = buf[:-1]
    else:
        if 'badlen2' in args:
            buf = buf[:-1]
    return buf

# When mocking a peripheral (for now) generate a data packet
def gen_data(buf, args):
    buf += gen_timestamp_peripheral()
    buf += gen_tid_peripheral()
    buf += args["payload"].replace("\\n", "\n").encode(args.get('encoding', 'utf-8'))
    return buf

# When mocking a peripheral (for now) generate a data packet with unsupported type
def gen_badtype(buf, args):
    buf += b'01234567'
    return buf

pkttypes = {"ts": (type_timestamp, gen_ts, broadcast_mac),
            "data": (type_data, gen_data, other_mac),
            "badtype": (66, gen_badtype, other_mac) }

def tx_packet(psk, group, channel, pkttypename, args):
    badpsk = list(psk)
    badpsk[0] = badpsk[0] + 1
    badpsk = bytes(badpsk)

    badgroup = list(group)
    badgroup[0] = badgroup[0] + 1
    badgroup = bytes(badgroup)

    pkttype, gen, dmac = pkttypes[pkttypename]
    buf = bytearray([('badversion' in args) and (version + 1) or version, pkttype])
    buf += ('badgroup' in args) and badgroup or group
    buf = gen(buf, args)
    if 'badlen' in args:
        buf = buf[0:2 + group_size - 1]
    buf = encrypt(('badcrypt' in args) and badpsk or psk, buf)
    buf += hmac(('badhmac' in args) and badpsk or psk, buf)

    packet = bytes([channel]) + dmac + my_mac + buf

    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    f = "%.9f.rx" % time.time()
    open(folder + f, "wb").write(packet)
