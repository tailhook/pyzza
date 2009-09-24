import pprint
import struct

from . import bytecode
from .io import ABCStream

class ABCStruct(object):

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__,
            pprint.pformat(self.__dict__))

class CPoolInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.int_count = stream.read_u30()
        self.integer = [stream.read_s32() for i in range(self.int_count)]
        self.uint_count = stream.read_u30()
        self.uinteger = [stream.read_u32() for i in range(self.uint_count)]
        self.double_count = stream.read_u30()
        self.double = [stream.read_d64() for i in range(self.double_count)]
        self.string_count = stream.read_u30()
        self.string = [stream.read(stream.read_u30()).decode('utf-8')
            for i in range(self.string_count-1)]
        self.namespace_count = stream.read_u30()
        self.namespace_info = [NamespaceInfo.read(stream)
            for i in range(self.namespace_count-1)]
        self.ns_set_count = stream.read_u30()
        self.ns_set_info = [NamespaceSetInfo.read(stream)
            for i in range(self.ns_set_count-1)]
        self.multiname_count = stream.read_u30()
        self.multiname_info = [MultinameInfo.read(stream)
            for i in range(self.multiname_count-1)]
        return self

class NamespaceInfo(ABCStruct):
    CONSTANT_Namespace          = 0x08
    CONSTANT_PackageNamespace   = 0x16
    CONSTANT_PackageInternalNs  = 0x17
    CONSTANT_ProtectedNamespace = 0x18
    CONSTANT_ExplicitNamespace  = 0x19
    CONSTANT_StaticProtectedNs  = 0x1A
    CONSTANT_PrivateNs          = 0x05
    kinds = (
        CONSTANT_Namespace,
        CONSTANT_PackageNamespace,
        CONSTANT_PackageInternalNs,
        CONSTANT_ProtectedNamespace,
        CONSTANT_ExplicitNamespace,
        CONSTANT_StaticProtectedNs,
        CONSTANT_PrivateNs,
        )

    @classmethod
    def read(cls, stream):
        self = cls()
        self.kind = stream.read_u8()
        assert self.kind in self.kinds, "Wrong kind {}".format(self.kind)
        self.name = stream.read_u30()
        return self

    def repr(self, cpool):
        return '<NS{:d}:{:s}>'.format(self.kind, cpool.string[self.name-1])

class NamespaceSetInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.count = stream.read_u30()
        self.ns = [stream.read_u30()
            for i in range(self.count)]
        return self

    def repr(self, cpool):
        return '<Ns {}>'.format(
            ','.join(cpool.namespace_info[n-1].repr(cpool)
                for n in self.ns))

class MethodInfo(ABCStruct):
    NEED_ARGUMENTS = 0x01
    NEED_ACTIVATION = 0x02
    NEED_REST = 0x04
    HAS_OPTIONAL = 0x08
    SET_DXNS = 0x40
    HAS_PARAM_NAMES = 0x80

    @classmethod
    def read(cls, stream):
        self = cls()
        self.param_count = stream.read_u30()
        self.return_type = stream.read_u30()
        self.param_type = [stream.read_u30()
            for i in range(self.param_count)]
        self.name = stream.read_u30()
        self.flags = stream.read_u8()
        if self.flags & self.HAS_OPTIONAL:
            self.options = OptionInfo.read(stream)
        if self.flags & self.HAS_PARAM_NAMES:
            self.param_name = [stream.read_u30()
                for i in range(self.param_count)]
        return self

class OptionDetail(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.val = stream.read_u30()
        self.kind = stream.read_u8()
        return self

class OptionInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.option_count = stream.read_u30()
        self.option = [OptionDetail.read(stream)
            for i in range(self.option_count)]
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

class MultinameInfo(ABCStruct):
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

    @classmethod
    def read(cls, stream):
        self = cls()
        self.kind = stream.read_u8()
        if self.kind in (self.CONSTANT_QName, self.CONSTANT_QNameA):
            self.ns = stream.read_u30()
            self.name = stream.read_u30()
        elif self.kind in (self.CONSTANT_RTQName, self.CONSTANT_RTQNameA):
            self.name = stream.read_u30()
        elif self.kind in (self.CONSTANT_RTQNameL, self.CONSTANT_RTQNameLA):
            pass
        elif self.kind in (self.CONSTANT_Multiname, self.CONSTANT_Multiname):
            self.name = stream.read_u30()
            self.ns_set = stream.read_u30()
        elif self.kind in (self.CONSTANT_MultinameL, self.CONSTANT_MultinameL):
            self.ns_set = stream.read_u30()
        else:
            raise NotImplementedError(self.kind)
        return self

    def repr(self, cpool):
        val = '<MN:'
        if hasattr(self, 'name'):
            val += cpool.string[self.name-1]
        val += ':'
        if hasattr(self, 'ns'):
            val += cpool.namespace_info[self.ns-1].repr(cpool)
        elif hasattr(self, 'ns_set'):
            val += cpool.ns_set_info[self.ns_set-1].repr(cpool)
        return val + '>'

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
        self.method_count = stream.read_u30()
        self.method_info = [MethodInfo.read(stream)
            for i in range(self.method_count)]
        self.metadata_count = stream.read_u30()
        self.metadata_info = [MetadataInfo.read(stream)
            for i in range(self.metadata_count)]
        self.class_count = stream.read_u30()
        self.instance_info = [InstanceInfo.read(stream)
            for i in range(self.class_count)]
        self.class_info = [ClassInfo.read(stream)
            for i in range(self.class_count)]
        self.script_count = stream.read_u30()
        self.script_info = [ScriptInfo.read(stream)
            for i in range(self.script_count)]
        self.method_body_count = stream.read_u30()
        self.method_body_info = [MethodBodyInfo.read(stream)
            for i in range(self.method_body_count)]
        assert not stream.read(1)
        return self


class DoABC(object):

    def readbody(self, file):
        self.data = file.read(self.length)
        self.flags = struct.unpack('<L', self.data[:4])[0]
        idx = self.data.index(b'\x00', 4)
        self.name = self.data[4:idx].decode('utf-8')
        self.body = self.data[idx+1:]

    def decode(self):
        abc = ABCStream(self.body)
        self.real_body = ABCFile.read(abc)

    def print(self):
        for i in range(self.real_body.method_body_count):
            body = self.real_body.method_body_info[i]
            head = self.real_body.method_info[body.method]
            print("METHOD",
                self.real_body.constant_pool.string[head.name-1],
                "PARAMS", head.param_count)
            for i in body.bytecode:
                i.print(self.real_body.constant_pool)

