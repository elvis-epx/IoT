# Unit tests of our protocol for ESP-NOW

from epx.netnow import *

mac = '0A:1B:22:33:44:5F'
macb = b'\x0a\x1b\x22\x33\x44\x5f'

assert(mac_s2b(mac) == macb)
assert(mac_b2s(macb) == mac)

assert(b2s(b'\xba\xbe') == "BA:BE")
n = 666
assert(decode_timestamp(encode_timestamp(n)) == n)

assert(gen_tid() != gen_tid())
assert(gen_initial_timestamp() != gen_initial_timestamp())

assert(group_hash(b'bla') != group_hash(b'ble'))
assert(len(group_hash(b'abc')) == group_size)
assert(len(prepare_key(b'abc')) == hash_size)

assert(xor(b'\x01', b'\x02\x04') == b'\x03\x04')
assert(xor(b'\x02\x04', b'\x01') == b'\x03\x04')
assert(xor(b'\x02\x04', b'\x01\x02') == b'\x03\x06')

assert(hmac(b'k1', b'') == hmac(b'k1', b''))
assert(hmac(b'k1', b'') != hmac(b'k2', b''))
assert(hmac(b'k1', b'bla') != hmac(b'k1', b'ble'))
assert(hmac(b'k1', b'bla') != hmac(b'k2', b'bla'))
assert(hmac(b'k1', b'bla') == hmac(b'k1', b'bla'))
assert(len(hmac(b'k1', b'bla'))) == 12
assert(check_hmac(b'k1', b'bla' + hmac(b'k1', b'bla')))
assert(not check_hmac(b'k2', b'bla' + hmac(b'k1', b'bla')))
assert(not check_hmac(b'k1', b'bla' + hmac(b'k1', b'ble')))
assert(not check_hmac(b'k1', b'abracadabra'))
assert(not check_hmac(b'k1', b''))

k1 = b'bla' + b'\x00' * 28
k2 = b'bla' + b'\x00' * 29
k3 = b'bla' + b'\x00' * 30
assert(prepare_key(k1) == k2)
assert(prepare_key(k2) == k2)
assert(prepare_key(k3) != k3)

for n in range(0, 50):
    payload = b'p' * n
    enc = encrypt(b'k' * 32, b'p' * n)
    assert(len(enc) % 16 == 0)
    dec = decrypt(b'k' * 32, enc)
    assert(dec == payload)
    assert(decrypt(b'k' * 32, enc[:-1]) is None)
    assert(decrypt(b'k' * 32, b'b' * n) is None)
