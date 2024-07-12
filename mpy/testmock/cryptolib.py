from Cryptodome.Cipher import AES

class aes:
    def __init__(self, key, mode, iv):
        self.impl = AES.new(key, mode, iv)
    def encrypt(self, msg):
        return self.impl.encrypt(msg)
    def decrypt(self, msg):
        return self.impl.decrypt(msg)
