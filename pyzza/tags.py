from . import io

TAG_ShowFrame = 1
TAG_PlaceObject = 4
TAG_RemoveObject = 5
TAG_SetBackgroundColor = 9
TAG_Protect = 24
TAG_RemoveObject2 = 28
TAG_PlaceObject2 = 26
TAG_FrameLabel = 43
TAG_ExportAssets = 56
TAG_ImportAssets = 57
TAG_EnableDebugger = 58
TAG_EnableDebugger2 = 64
TAG_ScriptLimits = 65
TAG_SetTabIndex = 66
TAG_FileAttributes = 69
TAG_PlaceObject3 = 70
TAG_ImportAssets2 = 71
TAG_SymbolClass = 76
TAG_Metadata = 77
TAG_DefineScalingGrid = 78
TAG_DefineSceneAndFrameLabelData = 86
TAG_DoABC = 82
TAG_End = 0

class Tag(object):
    code = None
    length = None

    def blob(self):
        res = bytearray()
        if self.length > 62:
            res += bytes([
                ((self.code << 6) | 0x3f) & 0xFF,
                (self.code << 6) >> 8])
            res += bytes([
                self.length & 0xFF,
                (self.length >> 8) & 0xFF,
                (self.length >> 16) & 0xFF,
                (self.length >> 24) & 0xFF,
                ])
        else:
            res += bytes([
                ((self.code & 0x3) << 6) | self.length,
                self.code >> 2])
        res += self.data
        return res

    def _read(self, stream):
        self.data = stream.readbytes(self.length).bytes

    def __repr__(self):
        return '<{0} type:{1} len:{2}>'.format(self.__class__.__name__,
            self.code, self.length)

class End(Tag):
    code = TAG_End

    def blob(self):
        self.data = b''
        return super().blob()

    def _read(self, stream):
        assert self.length == 0, self.length

class SymbolClass(Tag):
    code = TAG_SymbolClass

    def __init__(self, main_class=None):
        if main_class is not None:
            self.assoc = { 0: main_class }

    def _read(self, stream):
        self.number = stream.readbytes(2).int_le
        self.assoc = {}
        for i in range(self.number):
            k = stream.readbytes(2).int_le
            self.assoc[k] = stream.readstring()

    def blob(self):
        self.number = len(self.assoc)
        self.data = bytearray([self.number & 0xFF, self.number >> 8])
        for (k, v) in self.assoc.items():
            self.data.extend([k >> 8, k & 0xFF])
            self.data.extend(v.encode('utf-8'))
            self.data.append(0)
        self.length = len(self.data)
        return super().blob()

    def __repr__(self):
        return '<{0} {1!r}>'.format(self.__class__.__name__, self.assoc)

class FileAttributes(Tag):
    code = TAG_FileAttributes

    def __init__(self):
        self.r1 = 0
        self.UseDirectBlit = False
        self.UseGPU = True
        self.HasMetadata = False
        self.ActionScript3 = True
        self.r2 = 0
        self.UseNetwork = True
        self.r3 = 0

    def _read(self, stream):
        self.r1 = stream.readbits(1)
        self.UseDirectBlit = bool(stream.readbits(1))
        self.UseGPU = bool(stream.readbits(1))
        self.HasMetadata = bool(stream.readbits(1))
        self.ActionScript3 = bool(stream.readbits(1))
        self.r2 = stream.readbits(2)
        self.UseNetwork = bool(stream.readbits(1))
        self.r3 = stream.readbits(24)

    def blob(self):
        self.HasMetadata = False
        byte = ((self.r1 << 7)
            | (int(self.UseDirectBlit) << 6)
            | (int(self.UseGPU) << 5)
            | (int(self.HasMetadata) << 4)
            | (int(self.ActionScript3) << 3)
            | ((int(self.r2) << 1) & 0x3)
            | int(self.UseNetwork))
        self.data = bytes([
            byte,
            self.r3 & 0xFF,
            (self.r3 >> 8) & 0xFF,
            (self.r3 >> 16) & 0xFF,
            ])
        self.length = len(self.data)
        return super().blob()

class ShowFrame(Tag):
    code = TAG_ShowFrame

    def blob(self):
        self.length = 0
        self.data = b''
        return super().blob()

from .abc import DoABC

tag_classes = {}
for v in list(globals().values()):
    if isinstance(v, type) and issubclass(v, Tag) and v is not Tag:
        tag_classes[v.code] = v
del v

def read(file):
    stream = io.BitStream(file)
    mark = stream.readbytes(2).int_le
    code = mark >> 6
    if code in tag_classes:
        self = tag_classes[code]()
    else:
        self = Tag()
    self.code = code
    self.length = mark & 63
    if self.length == 0x3f:
        self.length = stream.readbytes(4).int_le
    self._read(stream)
    return self
