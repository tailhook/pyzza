from io import BytesIO
import struct

class ABCStream(object):

    def __init__(self, bytes):
        if hasattr(bytes, 'read'):
            self._stream = bytes
        else:
            self._stream = BytesIO(bytes)

    def read_s24(self):
        bytes = self._stream.read(3)
        res = bytes[0] | (bytes[1] << 8) | (bytes[2] << 16)
        if res > (1 << 23):
            res = -((~res)&((1 << 23)-1))
        return res

    def read_u16(self):
        bytes = self._stream.read(2)
        return bytes[0] | (bytes[1] << 8)

    def read_u8(self):
        return self._stream.read(1)[0]

    def read_u30(self):
        res = 0
        for i in range(5):
            b = self._stream.read(1)
            res |= (b[0] & 127) << (i*7)
            if not (b[0] & 128):
                break
        assert res < (1 << 30)
        return res

    def read_s32(self):
        res = 0
        for i in range(5):
            b = self._stream.read(1)
            if b[0] & 128:
                res |= (b[0] & 127) << (i*7)
            else:
                res |= (b[0] & 63) << (i*7)
                if b[0] & 64:
                    res = -res
                break
        assert res < (1 << 32)
        return res

    def read_u32(self):
        res = 0
        for i in range(5):
            b = self._stream.read(1)
            res |= (b[0] & 127) << (i*7)
            if not (b[0] & 128):
                break
        assert res < (1 << 32)
        return res

    def read_d64(self):
        return struct.unpack('d', self._stream.read(8))

    def read(self, num):
        return self._stream.read(num)
