import zlib
import struct
from io import BytesIO
from math import log, ceil
from operator import methodcaller

from . import bitstream, tags

class Rect(object):
    x_min = None
    x_max = None
    y_min = None
    y_max = None

    def __init__(self, width=None, height=None):
        self.x_min = 0
        self.y_min = 0
        self.x_max = width
        self.y_max = height

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

    def __init__(self, compressed=True, version=10, frame_size=(10000,7500),
        frame_rate=(15<<8), frame_count=1):
        self.compressed = compressed
        self.version = version
        self.frame_size = Rect(*frame_size)
        self.frame_rate = frame_rate
        self.frame_count = frame_count

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
            raise ValueError("Wrong signature ``{0}''".format(sig))
        self.version = stream.readbytes(1).int_le
        self.file_length = stream.readbytes(4).int_le
        if self.compressed:
            buf = zlib.decompress(file.read())
            assert len(buf)+8 == self.file_length,\
                '{0} {1}'.format(len(buf), self.file_length)
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

def get_options():
    import optparse
    op = optparse.OptionParser()
    op.add_option('-p', '--print-tags',
        help='Print tags while decoding SWF file',
        dest="print_tags", default=False, action="store_true")
    op.add_option('-P', '--print-abcfile',
        help='Print abcFile structure while decoding SWF file',
        dest="print_abcfile", default=False, action="store_true")
    op.add_option('-d', '--disassemble',
        help='Print bytecode disassemble while decoding ABC',
        dest="print_dis", default=False, action="store_true")
    op.add_option('-O', '--optimize',
        help='Optimize bytecode',
        dest="optimize", default=False, action="store_true")
    op.add_option('-s', '--strip',
        help='Strip unneeded tags (assumes that you have code-only file without'
            ' graphic or other content)',
        dest="strip", default=False, action="store_true")
    op.add_option('-o', '--output', metavar="FILE",
        help='Write output swf into FILE',
        dest="output", default=None, type="string")
    return op

def main():
    global options
    op = get_options()
    options, args = op.parse_args()

    if len(args) != 1:
        op.error("Exacly one argument expected")

    with open(args[0], 'rb') as f:
        h = Header.read(f)
        if options.print_tags:
            print(h)
        tag = None
        taglist = []
        while not isinstance(tag, tags.End):
            tag = tags.read(h.file)
            taglist.append(tag)
            if options.print_tags:
                print(tag)
            if options.print_abcfile and isinstance(tag, tags.DoABC):
                from . import pretty
                pretty.pprint(tag.real_body)
            if options.print_dis and hasattr(tag, 'disassemble'):
                tag.disassemble()

    if options.output:
        if options.optimize:
            from . import fastbytes
            for tag in taglist:
                if isinstance(tag, tags.DoABC):
                    tag.clean_metadata()
                    fastbytes.optimize(tag)
        if options.strip:
            good_tags = (
                tags.DoABC,
                tags.SymbolClass,
                tags.ShowFrame,
                tags.FileAttributes,
                )
            taglist = (tag for tag in taglist if isinstance(tag, good_tags))
        content = b''.join(map(methodcaller('blob'), taglist))
        with open(options.output, 'wb') as outfile:
            h.write_swf(outfile, content)

if __name__ == '__main__':

    from . import swf
    swf.main()
