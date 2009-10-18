from io import BytesIO
import struct

s24 = 's24'
u16 = 'u16'
u8 = 'u8'
u30 = 'u30'
s32 = 's32'
u32 = 'u32'
d64 = 'd64'

class ABCStream(BytesIO):

    def read_formatted(self, format):
        return getattr(self, 'read_' + format)()

    def read_s24(self):
        bytes = self.read(3)
        res = bytes[0] | (bytes[1] << 8) | (bytes[2] << 16)
        if res > (1 << 23):
            res = -((~res)&((1 << 23)-1))
        return res

    def write_s24(self, val):
        if val < 0:
            val = -val | (1 << 24)
        assert val < (1 << 23)
        self.write(bytes([val & 0xFF,
            ((val >> 8) & 0xFF),
            val >> 16]))

    def read_u16(self):
        bytes = self.read(2)
        return bytes[0] | (bytes[1] << 8)

    def write_u16(self, val):
        assert 0 <= val < 1 << 16
        self.write(bytes([
            val & 0xFF,
            val >> 8]))

    def read_u8(self):
        return self.read(1)[0]

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
        return res

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
        return res

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
