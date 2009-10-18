import pprint
import struct

from .tags import Tag, TAG_DoABC
from .io import ABCStream

class Undefined(object):
    def __new__(cls):
        global undefined
        try:
            return undefined
        except NameError:
            undefined = super().__new__(cls)
            return undefined

class ABCStruct(object):
    pass

class CPoolInfo(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        index = Index(self)
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
        self.namespace_info = [NamespaceInfo.read(stream, index)
            for i in range(namespace_count-1)]
        ns_set_count = stream.read_u30()
        self.ns_set_info = [NamespaceSetInfo.read(stream, index)
            for i in range(ns_set_count-1)]
        multiname_count = stream.read_u30()
        self.multiname_info = [MultinameInfo.read(stream, index)
            for i in range(multiname_count-1)]
        return self

    def write(self, stream, index):
        if self.integer:
            stream.write_u30(len(self.integer)+1)
            for i in self.integer:
                stream.write_s32(i)
        else:
            stream.write_u30(0)
        if self.uinteger:
            stream.write_u30(len(self.uinteger)+1)
            for i in self.uinteger:
                stream.write_u32(i)
        else:
            stream.write_u30(0)
        if self.double:
            stream.write_u30(len(self.double)+1)
            for i in self.double:
                stream.write_d64(i)
        else:
            stream.write_u30(0)
        if self.string:
            stream.write_u30(len(self.string)+1)
            for i in self.string:
                s = i.encode('utf-8')
                stream.write_u30(len(s))
                stream.write(s)
        else:
            stream.write_u30(0)
        if self.namespace_info:
            stream.write_u30(len(self.namespace_info)+1)
            for ni in self.namespace_info:
                ni.write(stream, index)
        else:
            stream.write_u30(0)
        if self.ns_set_info:
            stream.write_u30(len(self.ns_set_info)+1)
            for ns in self.ns_set_info:
                ns.write(stream, index)
        else:
            stream.write_u30(0)
        if self.multiname_info:
            stream.write_u30(len(self.multiname_info)+1)
            for mi in self.multiname_info:
                mi.write(stream, index)
        else:
            stream.write_u30(0)

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
    def read(cls, stream, index):
        kind = stream.read_u8()
        ni = stream.read_u30()
        assert kind in namespace_kinds, "Wrong kind {}".format(kind)
        name = index.get_string(ni)
        self = namespace_kinds[kind](name)
        assert self.kind == kind
        return self

    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_string_index(self.name))

    def __repr__(self):
        return '<{:s} {:s}>'.format(self.__class__.__name__, self.name)

class NSUser(NamespaceInfo):
    kind = CONSTANT_Namespace
class NSPackage(NamespaceInfo):
    kind = CONSTANT_PackageNamespace
class NSInternal(NamespaceInfo):
    kind = CONSTANT_PackageInternalNs
class NSProtected(NamespaceInfo):
    kind = CONSTANT_ProtectedNamespace
class NSPrivate(NamespaceInfo):
    kind = CONSTANT_PrivateNs
class NSExplicit(NamespaceInfo):
    kind = CONSTANT_ExplicitNamespace
class NSStaticProtected(NamespaceInfo):
    kind = CONSTANT_StaticProtectedNs
class NSPrivate(NamespaceInfo):
    kind = CONSTANT_PrivateNs

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
    def read(cls, stream, index):
        self = cls()
        count = stream.read_u30()
        self.ns = [index.get_namespace(stream.read_u30())
            for i in range(count)]
        return self

    def write(self, stream, index):
        stream.write_u30(len(self.ns))
        for n in self.ns:
            stream.write_u30(index.get_namespace_index(n))

    def __repr__(self):
        return '<NS {}>'.format(','.join(map(repr, self.ns)))

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
    def read(cls, stream, index):
        self = cls()
        param_count = stream.read_u30()
        self.return_type = index.get_multiname(stream.read_u30())
        self.param_type = [index.get_multiname(stream.read_u30())
            for i in range(param_count)]
        self.name = index.get_string(stream.read_u30())
        self.flags = stream.read_u8()
        if self.flags & self.HAS_OPTIONAL:
            option_count = stream.read_u30()
            self.options = [OptionDetail.read(stream, index)
                for i in range(option_count)]
        if self.flags & self.HAS_PARAM_NAMES:
            self.param_name = [index.get_string(stream.read_u30())
                for i in range(param_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(len(self.param_type))
        stream.write_u30(index.get_multiname_index(self.return_type))
        for param in self.param_type:
            stream.write_u30(index.get_multiname_index(param))
        stream.write_u30(index.get_string_index(self.name))
        if hasattr(self, 'options'):
            self.flags |= self.HAS_OPTIONAL
        else:
            self.flags &= ~self.HAS_OPTIONAL
        if hasattr(self, 'param_name'):
            self.flags |= self.HAS_PARAM_NAMES
        else:
            self.flags &= ~self.HAS_PARAM_NAMES
        stream.write_u8(self.flags)
        if hasattr(self, 'options'):
            for o in self.options:
                o.write(stream, index)
        if hasattr(self, 'param_name'):
            assert len(self.param_name) == len(self.param_type)
            for p in self.param_name:
                stream.write_u30(index.get_string_index(p))

    def __repr__(self):
        return '<{} {!r} at {:x}>'.format(self.__class__.__name__,
            self.name, id(self))

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
    def read(cls, stream, index):
        self = cls()
        val = stream.read_u30()
        kind = stream.read_u8()
        self.value = index.get_constant(kind, val)
        return self

    def write(self, stream, index):
        kind, val = index.get_constant_index(self.value)
        stream.write_u30(val)
        stream.write_u8(kind)

class TraitSlot(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.slot_id = stream.read_u30()
        self.type_name = index.get_multiname(stream.read_u30())
        vindex = stream.read_u30()
        if vindex:
            vkind = stream.read_u8()
            self.value = index.get_constant(vkind, vindex)
        return self

    def write(self, stream, index):
        stream.write_u30(self.slot_id)
        stream.write_u30(index.get_multiname_index(self.type_name))
        if hasattr(self, 'value'):
            kind, index = index.get_constant_index(self.value)
            stream.write_u30(index)
            stream.write_u30(kind)
        else:
            stream.write_u30(0)

class TraitClass(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.slot_id = stream.read_u30()
        self.classi = index.get_class(stream.read_u30())
        return self

    def write(self, stream, index):
        stream.write_u30(self.slot_id)
        stream.write_u30(index.get_class_index(self.classi))

class TraitFunction(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.slot_id = stream.read_u30()
        self.function = index.get_method(stream.read_u30())
        return self

class TraitsInfo(ABCStruct):
    ATTR_Final = 0x01
    ATTR_Override = 0x02
    ATTR_Metadata = 0x04

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.name = index.get_string(stream.read_u30())
        byte = stream.read_u8()
        self.kind = byte & 15
        self.attr = byte >> 4
        if self.kind in (0, 6):
            self.data = TraitSlot.read(stream, index)
        elif self.kind == 4:
            self.data = TraitClass.read(stream, index)
        elif self.kind == 5:
            self.data = TraitFunction.read(stream, index)
        elif self.kind in (1, 2, 3):
            self.data = TraitMethod.read(stream, index)
        else:
            raise NotImplementedError(self.kind)

        if self.attr & self.ATTR_Metadata:
            metadata_count = stream.read_u30()
            self.metadata = [index.get_metadata(stream.read_u30())
                for i in range(metadata_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(index.get_string_index(self.name))
        if hasattr(self, 'metadata'):
            self.attr |= self.ATTR_Metadata
        else:
            self.attr &= ~self.ATTR_Metadata
        assert self.kind < 16
        byte = self.kind | (self.attr << 4)
        stream.write_u8(byte)
        self.data.write(stream, index)
        if hasattr(self, 'metadata'):
            stream.write_u30(len(self.metadata))
            for m in self.metadata:
                stream.write_u30(index.get_metadata_index(m))

class TraitMethod(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.disp_id = stream.read_u30()
        self.method = index.get_method(stream.read_u30())
        return self

    def write(self, stream, index):
        stream.write_u30(self.disp_id)
        stream.write_u30(index.get_method_index(self.method))

class ScriptInfo(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.init = index.get_method(stream.read_u30())
        trait_count = stream.read_u30()
        self.traits_info = [TraitsInfo.read(stream, index)
            for i in range(trait_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(index.get_method_index(self.init))
        stream.write_u30(len(self.traits_info))
        for t in self.traits_info:
            t.write(stream, index)

class MetadataInfo(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.name = index.get_string(stream.read_u30())
        item_count = stream.read_u30()
        self.item_info = [(index.get_string(stream.read_u30()),
            index.get_string(stream.read_u30()))
            for i in range(item_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(index.get_string_index(self.name))
        stream.write_u30(len(self.item_info))
        for (k, v) in self.item_info:
            stream.write_u30(index.get_string_index(k))
            stream.write_u30(index.get_string_index(v))

class MethodBodyInfo(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.method = index.get_method(stream.read_u30())
        self.max_stack = stream.read_u30()
        self.local_count = stream.read_u30()
        self.init_scope_depth = stream.read_u30()
        self.max_scope_depth = stream.read_u30()
        code_length = stream.read_u30()
        self.code = stream.read(code_length)
        exception_count = stream.read_u30()
        self.exception_info = [ExceptionInfo.read(stream, index)
            for i in range(exception_count)]
        trait_count = stream.read_u30()
        self.traits_info = [TraitsInfo.read(stream, index)
            for i in range(trait_count)]
        with index.for_method(self) as mindex:
            self.bytecode = bytecode.parse(self.code, mindex)
        return self

    def write(self, stream, index):
        with index.for_method(self) as mindex:
            self.code = bytecode.assemble(self.bytecode, mindex)
        stream.write_u30(index.get_method_index(self.method))
        stream.write_u30(self.max_stack)
        stream.write_u30(self.local_count)
        stream.write_u30(self.init_scope_depth)
        stream.write_u30(self.max_scope_depth)
        stream.write_u30(len(self.code))
        stream.write(self.code)
        stream.write_u30(len(self.exception_info))
        for exc in self.exception_info:
            exc.write(stream, index)
        stream.write_u30(len(self.traits_info))
        for t in self.traits_info:
            t.write(stream, index)

class ExceptionInfo(ABCStruct):

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.exc_from = stream.read_u30()
        self.exc_to = stream.read_u30()
        self.target = stream.read_u30()
        self.exc_type = index.get_multiname(stream.read_u30())
        self.var_name = index.get_multiname(stream.read_u30())
        return self

    def write(self, stream, index):
        stream.write_u30(self.exc_from)
        stream.write_u30(self.exc_to)
        stream.write_u30(self.target)
        stream.write_u30(index.get_multiname_index(self.exc_type))
        stream.write_u30(index.get_multiname_index(self.var_name))

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
        assert kind == self.kind
        self._read(stream, cpool)
        return self

class QName(MultinameInfo):
    kind = CONSTANT_QName
    def _read(self, stream, index):
        self.namespace = index.get_namespace(stream.read_u30())
        self.name = index.get_string(stream.read_u30())
    def __repr__(self):
        return '<{} {}:{}>'.format(self.__class__.__name__,
            self.namespace, self.name)
    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_namespace_index(self.namespace))
        stream.write_u30(index.get_string_index(self.name))
class QNameA(QName):
    kind = CONSTANT_QNameA
class RTQName(MultinameInfo):
    kind = CONSTANT_RTQName
    def _read(self, stream, cpool):
        self.name = cpool.string[stream.read_u30()-1]
    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.name)
    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_string_index(self.name))
class RTQNameA(RTQName):
    kind = CONSTANT_RTQNameA
class RTQNameL(MultinameInfo):
    kind = CONSTANT_RTQNameL
    def _read(self, stream, cpool): pass
    def __repr__(self):
        return '<RTQNameL>'
    def write(self, stream, index):
        stream.write_u8(self.kind)
class RTQNameLA(RTQNameL):
    kind = CONSTANT_RTQNameLA
class Multiname(MultinameInfo):
    kind = CONSTANT_Multiname
    def _read(self, stream, index):
        self.name = index.get_string(stream.read_u30())
        self.namespace_set = index.get_namespace_set(stream.read_u30())
    def __repr__(self):
        return '<{} {}:{}>'.format(self.__class__.__name__,
            self.namespace_set, self.name)
    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_namespace_set_index(self.namespace_set))
        stream.write_u30(index.get_string_index(self.name))
class MultinameA(Multiname):
    kind = CONSTANT_MultinameA
class MultinameL(MultinameInfo):
    kind = CONSTANT_MultinameL
    def _read(self, stream, index):
        self.namespace_set = index.get_namespace_set(stream.read_u30())
    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.namespace_set)
    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_namespace_set_index(self.namespace_set))
class MultinameLA(Multiname):
    kind = CONSTANT_MultinameLA

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
    def read(cls, stream, index):
        self = cls()
        self.name = index.get_multiname(stream.read_u30())
        self.super_name = index.get_multiname(stream.read_u30())
        self.flags = stream.read_u8()
        if self.flags & self.CONSTANT_ClassProtectedNs:
            self.protectedNs = stream.read_u30()
        intrf_count = stream.read_u30()
        self.interface = [index.get_multiname(stream.read_u30())
            for i in range(intrf_count)]
        self.iinit = index.get_method(stream.read_u30())
        trait_count = stream.read_u30()
        self.trait = [TraitsInfo.read(stream, index)
            for i in range(trait_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(index.get_multiname_index(self.name))
        stream.write_u30(index.get_multiname_index(self.super_name))
        if hasattr(self, 'protectedNs'):
            self.flags |= self.CONSTANT_ClassProtectedNs
        else:
            self.flags &= ~self.CONSTANT_ClassProtectedNs
        stream.write_u8(self.flags)
        if hasattr(self, 'protectedNs'):
            stream.write_u30(self.protectedNs)
        stream.write_u30(len(self.interface))
        for i in self.interface:
            stream.write_u30(index.get_multiname_index(i))
        stream.write_u30(index.get_method_index(self.iinit))
        stream.write_u30(len(self.trait))
        for i in self.trait:
            i.write(stream, index)

    def __repr__(self):
        return '<InstanceInfo {}({})>'.format(self.name, self.super_name)

class ClassInfo(ABCStruct):

    @classmethod
    def read(cls, stream, index, instance_info):
        self = cls()
        self.instance_info = instance_info
        self.cinit = index.get_method(stream.read_u30())
        trait_count = stream.read_u30()
        self.trait = [TraitsInfo.read(stream, index)
            for i in range(trait_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(index.get_method_index(self.cinit))
        stream.write_u30(len(self.trait))
        for t in self.trait:
            t.write(stream, index)

    def __repr__(self):
        return '<Class {}({})>'.format(self.instance_info.name,
            self.instance_info.super_name)

class Index(object):
    def __init__(self, data, method=None):
        if isinstance(data, CPoolInfo):
            self.cpool = data
        else:
            self.data = data
            self.cpool = data.constant_pool
        self._method = method

    def get_string(self, index):
        if index == 0:
            return ""
        return self.cpool.string[index-1]

    def get_string_index(self, value):
        #~ if value == '':
            #~ return 0
        return self.cpool.string.index(value)+1

    def get_integer(self, index):
        if index == 0:
            raise NotImplementedError()
        return self.cpool.integer[index-1]

    def get_integer_index(self, value):
        return self.cpool.integer.index(value)+1

    def get_uinteger(self, index):
        if index == 0:
            raise NotImplementedError()
        return self.cpool.uinteger[index-1]

    def get_uinteger_index(self, value):
        return self.cpool.uinteger.index(value)+1

    def get_multiname(self, index):
        if index == 0:
            return AnyType()
        return self.cpool.multiname_info[index-1]

    def get_multiname_index(self, multiname):
        if isinstance(multiname, AnyType):
            return 0
        return self.cpool.multiname_info.index(multiname)+1

    def get_namespace(self, index):
        if index == 0:
            raise NotImplementedError()
        return self.cpool.namespace_info[index-1]

    def get_namespace_index(self, namespace):
        return self.cpool.namespace_info.index(namespace)+1

    def get_namespace_set(self, index):
        return self.cpool.ns_set_info[index-1]

    def get_namespace_set_index(self, namespace_set):
        return self.cpool.ns_set_info.index(namespace_set)+1

    def get_double(self, index):
        if index == 0:
            raise NotImplementedError()
        return self.cpool.double[index-1]

    def get_double_index(self, value):
        return self.cpool.double.index(value) + 1

    def get_class(self, index):
        return self.data.class_info[index]

    def get_method(self, index):
        return self.data.method_info[index]

    def get_method_index(self, meth):
        return self.data.method_info.index(meth)

    def get_class_index(self, cls):
        return self.data.class_info.index(cls)

    def get_metadata(self, index):
        return self.data.metadata_info[index]

    def get_metadata_index(self, value):
        return self.data.metadata_info.index(value)

    def for_method(self, method):
        return Index(getattr(self, 'data', self.cpool), method)

    def get_exception_info(self, index):
        return self._method.exception_info[index]

    def get_exception_info_index(self, value):
        return self._method.exception_info.index(value)

    def get_constant(self, kind, val):
        if kind == CONSTANT_Int:
            return self.get_integer(val)
        elif kind == CONSTANT_UInt:
            return self.get_uinteger(val)
        elif kind == CONSTANT_Double:
            return self.get_double(val)
        elif kind == CONSTANT_Utf8:
            return self.get_string(val)
        elif kind == CONSTANT_True:
            #~ assert not val, 'Value {} for CONSTANT_True'.format(val)
            return True
        elif kind == CONSTANT_False:
            #~ assert not val, 'Value {} for CONSTANT_False'.format(val)
            return False
        elif kind == CONSTANT_Null:
            return None
        elif kind == CONSTANT_Undefined:
            return Undefined()
        else:
            return self.get_namespace(val)

    def get_constant_index(self, value):
        if value is True:
            return CONSTANT_True, 0
        elif value is False:
            return CONSTANT_False, 0
        elif value is None:
            return CONSTANT_Null, 0
        elif isinstance(value, Undefined):
            return CONSTANT_Undefined, 0
        elif isinstance(value, float):
            return CONSTANT_Double, self.get_double_index(value)
        elif isinstance(value, int):
            return CONSTANT_Int, self.get_integer_index(value)
        elif isinstance(value, str):
            return CONSTANT_Utf8, self.get_string_index(value)
        else:
            return value.kind, self.get_namespace_index(value)

    def __enter__(self):
        return self

    def __exit__(self, A, B, C):
        del self.cpool
        del self._method

class ABCFile(ABCStruct):

    @classmethod
    def read(cls, stream):
        self = cls()
        self.minor_version = stream.read_u16()
        self.major_version = stream.read_u16()
        assert self.minor_version == 16
        assert self.major_version == 46
        self.constant_pool = CPoolInfo.read(stream)
        index = Index(self)
        method_count = stream.read_u30()
        self.method_info = [MethodInfo.read(stream, index)
            for i in range(method_count)]
        metadata_count = stream.read_u30()
        self.metadata_info = [MetadataInfo.read(stream, index)
            for i in range(metadata_count)]
        class_count = stream.read_u30()
        instance_info = [InstanceInfo.read(stream, index)
            for i in range(class_count)]
        self.class_info = [ClassInfo.read(stream, index, instance_info[i])
            for i in range(class_count)]
        script_count = stream.read_u30()
        self.script_info = [ScriptInfo.read(stream, index)
            for i in range(script_count)]
        method_body_count = stream.read_u30()
        self.method_body_info = [MethodBodyInfo.read(stream, index)
            for i in range(method_body_count)]
        assert not stream.read(1)
        return self

    def write(self, stream):
        index = Index(self)
        stream.write_u16(self.minor_version)
        stream.write_u16(self.major_version)
        self.constant_pool.write(stream, index)
        stream.write_u30(len(self.method_info))
        for i in self.method_info:
            i.write(stream, index)
        stream.write_u30(len(self.metadata_info))
        for i in self.metadata_info:
            i.write(stream, index)
        stream.write_u30(len(self.class_info))
        for i in self.class_info:
            i.instance_info.write(stream, index)
        for i in self.class_info:
            i.write(stream, index)
        stream.write_u30(len(self.script_info))
        for i in self.script_info:
            i.write(stream, index)
        stream.write_u30(len(self.method_body_info))
        for i in self.method_body_info:
            i.write(stream, index)

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
        for body in self.real_body.method_body_info:
            print("METHOD", body.method.name, "PARAMS",
                getattr(body.method, 'param_name', body.method.param_type))
            for i in body.bytecode:
                i.print(self.real_body.constant_pool)

    def blob(self):
        buf = ABCStream()
        prefix = struct.pack('<L', self.flags)+self.name.encode('utf-8')+b'\x00'
        olddata = self.data
        self.real_body.write(buf)
        self.data = prefix + buf.getvalue()
        self.length = len(self.data)
        return super().blob()

from . import bytecode
