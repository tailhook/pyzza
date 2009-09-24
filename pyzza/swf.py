from . import bitstream, abc
import zlib
import struct
from io import BytesIO

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
            self.file = BytesIO(zlib.decompress(file.read()))
            stream = bitstream.BitStream(self.file)
        else:
            self.file = file
        self.frame_size = Rect.read(stream)
        self.frame_rate = stream.readbytes(2).int_le
        self.frame_count = stream.readbytes(2).int_le
        self.stream = stream
        return self

    def __repr__(self):
        return "<Header z:{0} ver:{version} len:{file_length} "\
            "frames{{sz:{frame_size} rate:{frame_rate} cnt:{frame_count}}}>"\
            .format('1' if self.compressed else '0', **self.__dict__)

class Tag(object):
    code = None
    length = None

    @staticmethod
    def read(file):
        stream = bitstream.BitStream(file)
        mark = stream.readbytes(2).int_le
        code = mark >> 6
        if code == 82:
            self = abc.DoABC()
        else:
            self = Tag()
        self.code = code
        self.length = mark & 63
        if self.length == 0x3f:
            self.length = stream.readbytes(4).int_le
        return self

    def skip(self, file):
        file.seek(self.length, 1)

    def __repr__(self):
        return '<Tag type:{} len:{}>'.format(self.code, self.length)

if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as f:
        h = Header.read(f)
        while True:
            tag = Tag.read(h.file)
            if tag.code == 0:
                break
            elif isinstance(tag, abc.DoABC):
                tag.readbody(h.file)
                tag.decode()
                tag.print()
            else:
                tag.skip(h.file)
