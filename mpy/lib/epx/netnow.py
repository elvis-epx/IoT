import os
from hashlib import sha256

broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
version = const(0x02)

type_data = const(0x01)

type_timestamp = const(0x02)
timestamp_subtype_default = const(0x00)
timestamp_subtype_confirm = const(0x01)

type_ping = const(0x03)
type_pairreq = const(0x04)
type_wakeup = const(0x05)

def mac_s2b(s):
    return bytes(int(x, 16) for x in s.split(':'))

def mac_b2s(mac):
    return ':'.join([f"{b:02X}" for b in mac])

def b2s(data):
    return ':'.join([f"{b:02X}" for b in data])

group_size = const(8)
hmac_size = const(12)
tid_size = const(12)
timestamp_size = const(12)

def decode_timestamp(b):
    return int.from_bytes(b, 'big')

def gen_initial_timestamp():
    b = bytearray(os.urandom(timestamp_size))
    b[0] &= 0x7f
    return decode_timestamp(b)

def encode_timestamp(n):
    return n.to_bytes(timestamp_size, 'big')

def gen_tid():
    return os.urandom(tid_size)

hash_size = 32

def _hash(data):
    h = sha256()
    h.update(data)
    return h.digest()

def group_hash(group):
    return _hash(group)[0:group_size]

def prepare_key(key):
    if len(key) <= hash_size:
        return key + bytearray([ 0x00 for _ in range(len(key), hash_size)])
    return _hash(key)

def xor(a, b):
    if len(a) > len(b):
        a, b = b, a
    return bytes(x ^ y for x, y in zip(a, b)) + b[len(a):]

ipad = bytearray( 0x36 for _ in range(0, hash_size))
opad = bytearray( 0x5c for _ in range(0, hash_size))

def hmac(key, data):
    return _hash(xor(key, opad) + _hash(xor(key, ipad) + data))[:hmac_size]

def check_hmac(key, data):
    return hmac(key, data[:-hmac_size]) == data[-hmac_size:]
