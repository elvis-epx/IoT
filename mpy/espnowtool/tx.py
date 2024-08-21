from espnowtool.utils import *
import time
import os

def gen_ts(buf, args):
    if 'confirm' not in args:
        subtype = timestamp_subtype_default
    else:
        subtype = timestamp_subtype_confirm
        tid = args['confirm']
    buf += bytearray([subtype])
    buf += gen_tid()
    timestamp = int(time.time() * 1000)
    buf += encode_timestamp(timestamp)
    if subtype == timestamp_subtype_confirm:
        buf += tid
    return buf

pkttypes = {"ts": (type_timestamp, gen_ts) }

def tx_packet(psk, group, channel, pkttypename, **extra):
    pkttype, gen = pkttypes[pkttypename]
    buf = bytearray([version, pkttype])
    buf += group
    buf = gen(buf, extra)
    buf = encrypt(psk, buf)
    buf += hmac(psk, buf)

    # TODO unicast dmac
    packet = bytes([channel]) + broadcast_mac + my_mac + buf

    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    f = "%.9f.rx" % time.time()
    open(folder + f, "wb").write(packet)
