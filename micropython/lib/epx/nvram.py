import esp32

class NVRAM:
    def __init__(self, namespace):
        self.impl = esp32.NVS(namespace)

    def set_int(self, key, n):
        self.impl.set_i32(key, n)
        self.impl.commit()

    def set_str(self, key, s):
        blob = s.encode('utf-8')
        self.impl.set_blob(key, blob)
        self.impl.set_i32(key + "_len", len(blob))
        self.impl.commit()

    def get_int(self, key):
        try:
            return self.impl.get_i32(key)
        except OSError:
            print("nvram: int %s not found" % key)
            return None

    def get_str(self, key):
        try:
            l = self.impl.get_i32(key + "_len")
        except OSError:
            print("nvram: str %s len not found" % key)
            return None

        buffer = bytearray(l)
        try:
            self.impl.get_blob(key, buffer)
        except OSError:
            print("nvram: str %s not found" % key)
            return None

        try:
            return bytes(buffer).decode('utf-8')
        except UnicodeDecodeError:
            print("nvram: str %s decode error" % key)
            return None
