import pprint
import struct

from . import bytecode
from .tags import Tag, TAG_DoABC
from .io import ABCStream

class ABCStruct(object):
    pass

class CPoolInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        int_count = stream.read_u30()
        self.integer = [stream.read_s32() for i in range(int_count-1)]
        uint_count = stream.read_u30()
        self.uinteger = [stream.read_u32() for i in range(uint_count-1)]
        double_count = stream.read_u30()
        self.double = [stream.read_d64() for i in range(double_count-1)]
        string_count = stream.read_u30()
        self.string = [stream.read(stream.read_u30()).decode('utf-8')
            for i in range(string_count-1)]
        namespace_count = stream.read_u30()
        self.namespace_info = [NamespaceInfo.read(stream, self)
            for i in range(namespace_count-1)]
        ns_set_count = stream.read_u30()
        self.ns_set_info = [NamespaceSetInfo.read(stream, self)
            for i in range(ns_set_count-1)]
        multiname_count = stream.read_u30()
        self.multiname_info = [MultinameInfo.read(stream, self)
            for i in range(multiname_count-1)]
        return self

CONSTANT_Namespace          = 0x08
CONSTANT_PackageNamespace   = 0x16
CONSTANT_PackageInternalNs  = 0x17
CONSTANT_ProtectedNamespace = 0x18
CONSTANT_ExplicitNamespace  = 0x19
CONSTANT_StaticProtectedNs  = 0x1A
CONSTANT_PrivateNs          = 0x05
class NamespaceInfo(ABCStruct):

    def __init__(self, name):
        self.name = name

    @classmethod
    def read(cls, stream, cpool):
        kind = stream.read_u8()
        assert kind in namespace_kinds, "Wrong kind {}".format(kind)
        name = stream.read_u30()
        if not name:
            name = ''
        else:
            name = cpool.string[name-1]
        self = namespace_kinds[kind](name)
        return self

    def __repr__(self):
        return '<{:s} {:s}>'.format(self.__class__.__name__, self.name)

class NSUser(NamespaceInfo): pass
class NSPackage(NamespaceInfo): pass
class NSInternal(NamespaceInfo): pass
class NSProtected(NamespaceInfo): pass
class NSPrivate(NamespaceInfo): pass
class NSExplicit(NamespaceInfo): pass
class NSStaticProtected(NamespaceInfo): pass
class NSPrivate(NamespaceInfo): pass

namespace_kinds = {
    CONSTANT_Namespace: NSUser,
    CONSTANT_PackageNamespace: NSPackage,
    CONSTANT_PackageInternalNs: NSInternal,
    CONSTANT_ProtectedNamespace: NSProtected,
    CONSTANT_ExplicitNamespace: NSExplicit,
    CONSTANT_StaticProtectedNs: NSStaticProtected,
    CONSTANT_PrivateNs: NSPrivate,
    }

class NamespaceSetInfo(ABCStruct):

    @classmethod
    def read(cls, stream, cpool):
        self = cls()
        count = stream.read_u30()
        self.ns = [cpool.namespace_info[stream.read_u30()]
            for i in range(count)]
        return self

    def repr(self, cpool):
        return '<Ns {}>'.format(','.join(self.ns))

class AnyType(object):
    __slots__ = ()

class MethodInfo(ABCStruct):
    NEED_ARGUMENTS = 0x01
    NEED_ACTIVATION = 0x02
    NEED_REST = 0x04
    HAS_OPTIONAL = 0x08
    SET_DXNS = 0x40
    HAS_PARAM_NAMES = 0x80

    @classmethod
    def read(cls, stream, cpool):
        self = cls()
        param_count = stream.read_u30()
        self.return_type = cpool.multiname_info[stream.read_u30()-1]
        self.param_type = [
            cpool.multiname_info[j] if j != 0 else AnyType()
            for j in (stream.read_u30()
            for i in range(param_count))]
        name = stream.read_u30()
        if name:
            self.name = cpool.string[name]
        else:
            self.name = ''
        self.flags = stream.read_u8()
        if self.flags & self.HAS_OPTIONAL:
            option_count = stream.read_u30()
            self.options = [OptionDetail.read(stream, cpool)
                for i in range(option_count)]
        if self.flags & self.HAS_PARAM_NAMES:
            self.param_name = [cpool.string[stream.read_u30()]
                for i in range(param_count)]
        return self
CONSTANT_Int                = 0x03
CONSTANT_UInt               = 0x04
CONSTANT_Double             = 0x06
CONSTANT_Utf8               = 0x01
CONSTANT_True               = 0x0B
CONSTANT_False              = 0x0A
CONSTANT_Null               = 0x0C
CONSTANT_Undefined          = 0x00
CONSTANT_Namespace          = 0x08
CONSTANT_PackageNamespace   = 0x16
CONSTANT_PackageInternalNs  = 0x17
CONSTANT_ProtectedNamespace = 0x18
CONSTANT_ExplicitNamespace  = 0x19
CONSTANT_StaticProtectedNs  = 0x1A
CONSTANT_PrivateNs          = 0x05

class OptionDetail(ABCStruct):

    @classmethod
    def read(cls, stream, cpool):
        self = cls()
        val = stream.read_u30()
        kind = stream.read_u8()
        if kind == CONSTANT_Int:
            self.value = cpool.integer[val]
        elif kind == CONSTANT_UInt:
            self.value = cpool.uinteger[val]
        elif kind == CONSTANT_Double:
            self.value = cpool.double[val]
        elif kind == CONSTANT_Utf8:
            self.value = cpool.string[val]
        elif kind == CONSTANT_True:
            assert not val
            self.value = True
        elif kind == CONSTANT_False:
            assert not val
            self.value = False
        elif kind == CONSTANT_Null:
            self.value = None
        elif kind == CONSTANT_Undefined:
            self.value = undefined
        else:
            self.value = cpool.namespace_info[val]
        return self

class ItemInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.key = stream.read_u30()
        self.value = stream.read_u30()
        return self

class TraitSlot(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.slot_id = stream.read_u30()
        self.type_name = stream.read_u30()
        self.vindex = stream.read_u30()
        if self.vindex:
            self.vkind = stream.read_u8()
        return self

class TraitClass(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.slot_id = stream.read_u30()
        self.classi = stream.read_u30()
        return self

class TraitFunction(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.slot_id = stream.read_u30()
        self.function = stream.read_u30()
        return self

class TraitsInfo(ABCStruct):
    ATTR_Final = 0x01
    ATTR_Override = 0x02
    ATTR_Metadata = 0x04

    @classmethod
    def read(cls, stream):
        self = cls()
        self.name = stream.read_u30()
        byte = stream.read_u8()
        self.kind = byte & 15
        self.attr = byte >> 4
        if self.kind in (0, 6):
            self.data = TraitSlot.read(stream)
        elif self.kind == 4:
            self.data = TraitClass.read(stream)
        elif self.kind == 5:
            self.data = TraitFunction.read(stream)
        elif self.kind in (1, 2, 3):
            self.data = TraitMethod.read(stream)
        else:
            raise NotImplementedError(self.kind)

        if self.attr & self.ATTR_Metadata:
            self.metadata_count = stream.read_u30()
            self.metadata = [stream.read_u30()
                for i in range(self.metadata_count)]
        return self

class TraitMethod(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.disp_id = stream.read_u30()
        self.method = stream.read_u30()
        return self

class ScriptInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.init = stream.read_u30()
        self.trait_count = stream.read_u30()
        self.traits_info = [TraitsInfo.read(stream)
            for i in range(self.trait_count)]
        return self

class MetadataInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.name = stream.read_u30()
        self.item_count = stream.read_u30()
        self.item_info = [ItemInfo.read(stream)
            for i in range(self.item_count)]
        return self

class MethodBodyInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.method = stream.read_u30()
        self.max_stack = stream.read_u30()
        self.local_count = stream.read_u30()
        self.init_scope_depth = stream.read_u30()
        self.max_scope_depth = stream.read_u30()
        self.code_length = stream.read_u30()
        self.code = stream.read(self.code_length)
        self.exception_count = stream.read_u30()
        self.exception_info = [ExceptionInfo.read(stream)
            for i in range(self.exception_count)]
        self.trait_count = stream.read_u30()
        self.traits_info = [TraitsInfo.read(stream)
            for i in range(self.trait_count)]
        self.bytecode = bytecode.parse(self.code)
        return self

class ExceptionInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.exc_from = stream.read_u30()
        self.exc_to = stream.read_u30()
        self.target = stream.read_u30()
        self.exc_type = stream.read_u30()
        self.var_name = stream.read_u30()
        return self

CONSTANT_QName       = 0x07
CONSTANT_QNameA      = 0x0D
CONSTANT_RTQName     = 0x0F
CONSTANT_RTQNameA    = 0x10
CONSTANT_RTQNameL    = 0x11
CONSTANT_RTQNameLA   = 0x12
CONSTANT_Multiname   = 0x09
CONSTANT_MultinameA  = 0x0E
CONSTANT_MultinameL  = 0x1B
CONSTANT_MultinameLA = 0x1C

class MultinameInfo(ABCStruct):

    @classmethod
    def read(cls, stream, cpool):
        kind = stream.read_u8()
        self = multiname_kinds[kind]()
        self._read(stream, cpool)
        return self

class QName(MultinameInfo):
    def _read(self, stream, cpool):
        self.namespace = cpool.namespace_info[stream.read_u30()-1]
        self.name = cpool.string[stream.read_u30()-1]
class QNameA(QName): pass
class RTQName(MultinameInfo):
    def _read(self, stream, cpool):
        self.name = cpool.string[stream.read_u30()-1]
class RTQNameA(RTQName): pass
class RTQNameL(MultinameInfo):
    def _read(self, stream, cpool): pass
class RTQNameLA(RTQNameL): pass
class Multiname(MultinameInfo):
    def _read(self, stream, cpool):
        self.name = cpool.string[stream.read_u30()-1]
        self.namespace_set = cpool.ns_set_info[stream.read_u30()-1]
class MultinameA(Multiname): pass
class MultinameL(MultinameInfo):
    def _read(self, stream, cpool):
        self.namespace_set = cpool.ns_set_info[stream.read_u30()-1]
class MultinameLA(Multiname): pass

multiname_kinds = {
    CONSTANT_QName: QName,
    CONSTANT_QNameA: QNameA,
    CONSTANT_RTQName: RTQName,
    CONSTANT_RTQNameA: RTQNameA,
    CONSTANT_RTQNameL: RTQNameL,
    CONSTANT_RTQNameLA: RTQNameLA,
    CONSTANT_Multiname: Multiname,
    CONSTANT_MultinameA: MultinameA,
    CONSTANT_MultinameL: MultinameL,
    CONSTANT_MultinameLA: MultinameLA,
    }

class InstanceInfo(ABCStruct):
    CONSTANT_ClassSealed = 0x01
    CONSTANT_ClassFinal  = 0x02
    CONSTANT_ClassInterface = 0x04
    CONSTANT_ClassProtectedNs = 0x08

    @classmethod
    def read(cls, stream):
        self = cls()
        self.name = stream.read_u30()
        self.super_name = stream.read_u30()
        self.flags = stream.read_u8()
        if self.flags & self.CONSTANT_ClassProtectedNs:
            self.protectedNs = stream.read_u30()
        self.intrf_count = stream.read_u30()
        self.interface = [stream.read_u30()
            for i in range(self.intrf_count)]
        self.iinit = stream.read_u30()
        self.trait_count = stream.read_u30()
        self.trait = [TraitsInfo.read(stream)
            for i in range(self.trait_count)]
        return self

class ClassInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.cinit = stream.read_u30()
        self.trait_count = stream.read_u30()
        self.trait = [TraitsInfo.read(stream)
            for i in range(self.trait_count)]
        return self

class ABCFile(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.minor_version = stream.read_u16()
        self.major_version = stream.read_u16()
        assert self.minor_version == 16
        assert self.major_version == 46
        self.constant_pool = CPoolInfo.read(stream)
        method_count = stream.read_u30()
        self.method_info = [MethodInfo.read(stream, self.constant_pool)
            for i in range(method_count)]
        metadata_count = stream.read_u30()
        self.metadata_info = [MetadataInfo.read(stream)
            for i in range(metadata_count)]
        class_count = stream.read_u30()
        self.instance_info = [InstanceInfo.read(stream)
            for i in range(class_count)]
        self.class_info = [ClassInfo.read(stream)
            for i in range(class_count)]
        script_count = stream.read_u30()
        self.script_info = [ScriptInfo.read(stream)
            for i in range(script_count)]
        method_body_count = stream.read_u30()
        self.method_body_info = [MethodBodyInfo.read(stream)
            for i in range(method_body_count)]
        assert not stream.read(1)
        return self


class DoABC(Tag):
    code = TAG_DoABC

    def __init__(self):
        pass

    def _read(self, stream):
        super()._read(stream)
        self.parse_body()
        self.decode()

    def parse_body(self):
        self.flags = struct.unpack('<L', self.data[:4])[0]
        idx = self.data.index(b'\x00', 4)
        self.name = self.data[4:idx].decode('utf-8')
        self.body = self.data[idx+1:]

    def decode(self):
        abc = ABCStream(self.body)
        self.real_body = ABCFile.read(abc)

    def print(self):
        from . import pretty
        pretty.pprint(self.real_body)
        for i in range(self.real_body.method_body_count):
            body = self.real_body.method_body_info[i]
            head = self.real_body.method_info[body.method]
            print("METHOD",
                self.real_body.constant_pool.string[head.name-1],
                "PARAMS", head.param_count)
            for i in body.bytecode:
                i.print(self.real_body.constant_pool)

    def blob(self):
        buf = BytesIO()
        buf.write(struct.pack('<L', self.flags))
        buf.write(self.name.encode('utf-8'))
        buf.write('\x00')
        self.real_body.write(buf)
        self.data = buf.getvalue()
        self.length = len(self.data)
        return super().blob()

