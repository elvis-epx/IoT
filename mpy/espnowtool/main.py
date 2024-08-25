import sys, time, os
from espnowtool.rx import *
from espnowtool.tx import *
from espnowtool.utils import group_hash, prepare_key

def usage():
    print("Usage: entool <psk> <group> <channel> tx <packet type> [<arg1> <value1>]...")
    print("              <psk> <group> <channel> rx <timeout> <packet type> [<arg1> <value1>]...")
    print("              <psk> <group> <channel> norx <timeout>")
    print("              flush [<arg1> <value1>]...")
    sys.exit(1)

def find_args(n):
    args = {}
    for i in range(n, len(sys.argv), 2):
        args[sys.argv[i]] = sys.argv[i+1]
    return args

def flush():
    args = find_args(2)
    flush_rx_packets(args)

def rx():
    psk = prepare_key(sys.argv[1].encode())
    group = group_hash(sys.argv[2].encode())
    channel = int(sys.argv[3])
    timeout = int(sys.argv[5]) + time.time()
    pkttype = sys.argv[6]
    args = find_args(7)

    pkt = rx_packet(psk, group, channel, timeout, pkttype, args)
    if pkt:
        print("entool: received expected packet")
        sys.exit(0)
    print("entool: failed to receive expected packet")
    sys.exit(1)

def norx():
    psk = prepare_key(sys.argv[1].encode())
    group = group_hash(sys.argv[2].encode())
    channel = int(sys.argv[3])
    timeout = int(sys.argv[5]) + time.time()
    args = find_args(6)

    pkt = rx_packet(psk, group, channel, timeout, "any", args)
    if pkt:
        print("entool: received unexpected packet")
        sys.exit(1)
    print("entool: no packet received (good)")
    sys.exit(0)

def tx():
    psk = prepare_key(sys.argv[1].encode())
    group = group_hash(sys.argv[2].encode())
    channel = int(sys.argv[3])
    pkttype = sys.argv[5]
    args = find_args(6)

    tx_packet(psk, group, channel, pkttype, args)

def mkdir():
    try:
        folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
        os.mkdir(folder)
    except OSError as e:
        # Most probably existing folder
        pass

def run():
    if len(sys.argv) >= 7 and sys.argv[4] == "rx":
        mkdir()
        rx()
    if len(sys.argv) >= 6 and sys.argv[4] == "norx":
        mkdir()
        norx()
    elif len(sys.argv) >= 6 and sys.argv[4] == "tx":
        mkdir()
        tx()
    elif len(sys.argv) >= 2 and sys.argv[1] == "flush":
        mkdir()
        flush()
    else:
        usage()
