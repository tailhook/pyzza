import zlib
import struct
from io import BytesIO
from math import log, ceil

from . import bitstream

class Rect(object):
    x_min = None
    x_max = None
    y_min = None
    y_max = None

    @classmethod
    def read(cls, bitstr):
        self = cls()
        bitlen = bitstr.readbits(5)
        self.x_min = bitstr.readbits(bitlen)
        self.x_max = bitstr.readbits(bitlen)
        self.y_min = bitstr.readbits(bitlen)
        self.y_max = bitstr.readbits(bitlen)
        return self

    def write(self, file):
        lg2 = log(2)
        bitlen = int(max(len(bin(int(getattr(self, a))))-1
            for a in ('x_min', 'x_max', 'y_min', 'y_max')))
        res = bitlen
        res <<= bitlen
        res |= self.x_min
        res <<= bitlen
        res |= self.x_max
        res <<= bitlen
        res |= self.y_min
        res <<= bitlen
        res |= self.y_max
        bytelen = ceil((5 + bitlen*4)/8.)
        res <<= bytelen*8 - (bitlen*4 + 5)
        val = bytes(reversed([(res >> (i*8))&0xFF
            for i in range(bytelen)]))
        file.write(val)

    def __repr__(self):
        return "<RECT {x_min} {x_max} {y_min} {y_max}>".format(**self.__dict__)

class Header(object):

    compressed = None
    version = None
    file_length = None
    frame_size = None
    frame_rate = None
    frame_count = None

    @classmethod
    def read(cls, file):
        stream = bitstream.BitStream(file)
        self = cls()
        sig = stream.readbytes(3).bytes
        if sig == b'FWS':
            self.compressed = False
        elif sig == b'CWS':
            self.compressed = True
        else:
            raise ValueError("Wrong signature ``{}''".format(sig))
        self.version = stream.readbytes(1).int_le
        self.file_length = stream.readbytes(4).int_le
        if self.compressed:
            buf = zlib.decompress(file.read())
            assert len(buf)+8 == self.file_length, '{} {}'.format(len(buf), self.file_length)
            self.file = BytesIO(buf)
            stream = bitstream.BitStream(self.file)
        else:
            self.file = file
        self.frame_size = Rect.read(stream)
        self.frame_rate = stream.readbytes(2).int_le
        self.frame_count = stream.readbytes(2).int_le
        self.stream = stream
        return self

    def write_swf(self, file, content):
        b = BytesIO()
        self.frame_size.write(b)
        b.write(bytes([
            self.frame_rate & 0xFF,
            (self.frame_rate >> 8) & 0xFF,
            ]))
        b.write(bytes([
            self.frame_count & 0xFF,
            (self.frame_count >> 8) & 0xFF,
            ]))
        content = b.getvalue() + content
        zcont = zlib.compress(content)
        self.file_length = len(content) + 8
        file.write(b'CWS')
        file.write(bytes([
            self.version,
            self.file_length & 0xFF,
            (self.file_length >> 8) & 0xFF,
            (self.file_length >> 16) & 0xFF,
            (self.file_length >> 24) & 0xFF,
            ]))
        file.write(zcont)

    def __repr__(self):
        return "<Header z:{0} ver:{version} len:{file_length} "\
            "frames{{sz:{frame_size} rate:{frame_rate} cnt:{frame_count}}}>"\
            .format('1' if self.compressed else '0', **self.__dict__)

def main():
    global abc
    from . import tags
    import sys
    with open(sys.argv[1]+'.swf', 'wb') as o:
        with open(sys.argv[1], 'rb') as f:
            h = Header.read(f)
            tag = None
            taglist = []
            while not isinstance(tag, tags.End):
                tag = tags.read(h.file)
                taglist.append(tag)
                print(tag)
                if hasattr(tag, 'print'):
                    tag.print()

            content = b''.join(t.blob() for t in taglist
                if t.code in (tags.TAG_DoABC, tags.TAG_SymbolClass,
                        tags.TAG_ShowFrame, tags.TAG_FileAttributes))
            h.write_swf(o, content)

if __name__ == '__main__':

    from . import swf
    swf.main()
