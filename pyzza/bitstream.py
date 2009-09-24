class Bytes(object):

    def __init__(self, bytes):
        self._bytes = bytes

    @property
    def int_be(self):
        res = 0
        for i in self._bytes:
            res = (res << 8) | i
        return res

    @property
    def int_le(self):
        res = 0
        for i in reversed(self._bytes):
            res = (res << 8) | i
        return res
    @property
    def sint_le(self):
        res = 0
        if self._bytes[0] > 128:
            res = - (self._bytes[0] & 127)
        else:
            res = self._bytes[0]
        for i in reversed(self._bytes[1:]):
            res = (res << 8) | i
        return res

    @property
    def bytes(self):
        return self._bytes

class BitStream(object):

    def __init__(self, stream):
        self._stream = stream
        self._buf = b''
        self._bitoffset = 0

    def readbytes(self, count):
        if self._buf:
            self._buf = b''
            self._bitoffset = 0
        return Bytes(self._stream.read(count))

    def readbits(self, count):
        if self._buf:
            if self._bitoffset + count >= 8:
                val = ((1 << (8 - self._bitoffset)) - 1) & self._buf[0]
                count -= 8 - self._bitoffset
                self._buf = b''
                self._bitoffset = 0
            else:
                val = ((1 << count)-1) & (self._buf[0] >> (8
                    - self._bitoffset + count))
                self._bitoffset += count
                return val
        else:
            val = 0
        bytes = count >> 3
        for i in range(bytes):
            byt = self._stream.read(1)
            val = (val << 8) | byt[0]
        tail = count & 7
        if tail:
            self._buf = self._stream.read(1)
            val <<= tail
            val |= self._buf[0] >> (8 - tail)
            self._bitoffset = tail
        return val
