from io import BytesIO
import struct

s24 = 's24'
u16 = 'u16'
u8 = 'u8'
u30 = 'u30'
s32 = 's32'
u32 = 'u32'
d64 = 'd64'

class uint(int):
    __slots__ = ()
    def __init__(self, val):
        assert self >= 0

class ABCStream(BytesIO):

    def read_formatted(self, format):
        return getattr(self, 'read_' + format)()

    def write_formatted(self, format, value):
        return getattr(self, 'write_' + format)(value)

    def read_s24(self):
        bytes = self.read(3)
        res = bytes[0] | (bytes[1] << 8) | (bytes[2] << 16)
        if res > (1 << 23):
            res = -((~res)&((1 << 23)-1))-1
        return res

    def write_s24(self, val):
        assert -(1 << 23) < val < (1 << 23)
        if val < 0:
            val = (1 << 24) + val
        self.write(bytes([val & 0xFF,
            ((val >> 8) & 0xFF),
            val >> 16]))

    def read_u16(self):
        bytes = self.read(2)
        return uint(bytes[0] | (bytes[1] << 8))

    def write_u16(self, val):
        assert 0 <= val < 1 << 16
        self.write(bytes([
            val & 0xFF,
            val >> 8]))

    def read_u8(self):
        return uint(self.read(1)[0])

    def write_u8(self, val):
        assert 0 <= val < 256
        self.write(bytes([ val ]))

    def read_u30(self):
        res = 0
        for i in range(5):
            b = self.read(1)
            res |= (b[0] & 127) << (i*7)
            if not (b[0] & 128):
                break
        assert res < (1 << 30)
        return uint(res)

    def write_u30(self, val):
        assert val < (1 << 30)
        while True:
            byte = val & 127
            val >>= 7
            if val:
                byte |= 128
            self.write(bytes([byte]))
            if not val:
                break

    def read_s32(self):
        res = 0
        for i in range(5):
            b = self.read(1)
            if b[0] & 128:
                res |= (b[0] & 127) << (i*7)
            else:
                res |= (b[0] & 63) << (i*7)
                if b[0] & 64:
                    res = -res
                break
        assert -(1 << 32) < res < (1 << 32)
        return res

    def write_s32(self, val):
        if val < 0:
            sign = 64
            val = -val
        else:
            sign = 0
        assert val < (1 << 32)
        while True:
            byte = val & 127
            val >>= 7
            if val:
                byte |= 128
            elif byte >= 64:
                byte |= 128
            else:
                byte |= sign
            self.write(bytes([byte]))
            if not (byte & 128):
                break

    def read_u32(self):
        res = 0
        for i in range(5):
            b = self.read(1)
            res |= (b[0] & 127) << (i*7)
            if not (b[0] & 128):
                break
        assert res < (1 << 32)
        return uint(res)

    def write_u32(self, val):
        assert 0 <= val < (1 << 32)
        while val:
            byte = val & 127
            val >>= 7
            if val:
                byte |= 128
            self.write(bytes([byte]))

    def read_d64(self):
        return struct.unpack('d', self.read(8))[0]

    def write_d64(self, val):
        self.write(struct.pack('d', val))

class DummyABCStream(object):
    for i in dir(ABCStream):
        if not i.startswith('__') and hasattr(getattr(ABCStream, i), '__call__'):
            locals()[i] = lambda *args: None

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

    def readstring(self):
        c = self._stream.read(1)
        res = bytearray()
        while c and c != b'\x00':
            res.extend(c)
            c = self._stream.read(1)
        return res.decode('utf-8')

    def readbits(self, count):
        if self._buf:
            if self._bitoffset + count >= 8:
                val = ((1 << (8 - self._bitoffset)) - 1) & self._buf[0]
                count -= 8 - self._bitoffset
                self._buf = b''
                self._bitoffset = 0
            else:
                val = ((1 << count)-1) & (self._buf[0] >> (8
                    - self._bitoffset - count))
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

