import struct
import copy
from operator import itemgetter
from collections import defaultdict

from .tags import Tag, TAG_DoABC
from .io import DummyABCStream, ABCStream, uint

nothing = object()

class Offset(int): pass
class Register(int): pass

class Undefined(object):
    def __new__(cls):
        global undefined
        try:
            return undefined
        except NameError:
            undefined = super().__new__(cls)
            return undefined

class ABCStruct(object):
    def __pretty__(self, p, cycle):
        if cycle:
            return '{0}(...)'.format(self.__class__.__name__)
        else:
            with p.group(4, self.__class__.__name__ + '(', ')'):
                for (idx, (k, v)) in enumerate(self.__dict__.items()):
                    if idx:
                        p.text(',')
                        p.breakable()
                    p.text(k + '=')
                    p.pretty(v)

class CPoolInfo(ABCStruct):

    def __init__(self):
        self.integer = []
        self.uinteger = []
        self.double = []
        self.string = []
        self.namespace_info = []
        self.ns_set_info = []
        self.multiname_info = []

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

    def __init__(self, name=''):
        assert isinstance(name, str)
        self.name = name

    @classmethod
    def read(cls, stream, index):
        kind = stream.read_u8()
        ni = stream.read_u30()
        assert kind in namespace_kinds, "Wrong kind {0}".format(kind)
        name = index.get_string(ni)
        self = namespace_kinds[kind](name)
        assert self.kind == kind
        return self

    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_string_index(self.name))

    def __repr__(self):
        return '<{0:s} {1:s}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return self.kind == other.kind and self.name == other.name

    def __hash__(self):
        return hash((self.kind, self.name))

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

    def __init__(self, *namespaces):
        self.ns = namespaces

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
        return '<NS {0}>'.format(','.join(map(repr, self.ns)))

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
            stream.write_u30(len(self.options))
            for o in self.options:
                o.write(stream, index)
        if hasattr(self, 'param_name'):
            assert len(self.param_name) == len(self.param_type)
            for p in self.param_name:
                stream.write_u30(index.get_string_index(p))

    def __repr__(self):
        return '<{0} {1!r} at {2:x}>'.format(self.__class__.__name__,
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

    def __init__(self, value):
        self.value = value

    @classmethod
    def read(cls, stream, index):
        val = stream.read_u30()
        kind = stream.read_u8()
        return cls(index.get_constant(kind, val))

    def write(self, stream, index):
        kind, val = index.get_constant_index(self.value)
        stream.write_u30(val)
        stream.write_u8(kind)

    def __repr__(self):
        return '<{0} {1!r}>'.format(self.__class__.__name__, self.value)

class TraitSlot(ABCStruct):
    kind = 0

    def __init__(self, slot_id=0, type_name=AnyType()):
        self.slot_id = slot_id
        self.type_name = type_name

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

    def __repr__(self):
        return '<{0} {1}:{2}{3}>'.format(self.__class__.__name__, self.slot_id,
            self.type_name, '=' + repr(getattr(self, 'value'))
            if hasattr(self, 'value') else '')

class TraitClass(ABCStruct):
    kind = 4

    def __init__(self, slot_id=0, classi=None):
        self.slot_id = slot_id
        self.classi = classi
        assert isinstance(classi, (type(None), ClassInfo))

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.slot_id = stream.read_u30()
        self.classi = index.get_class(stream.read_u30())
        return self

    def write(self, stream, index):
        stream.write_u30(self.slot_id)
        stream.write_u30(index.get_class_index(self.classi))

class TraitsInfo(ABCStruct):
    ATTR_Final = 0x01
    ATTR_Override = 0x02
    ATTR_Metadata = 0x04

    def __init__(self, name=None, data=None, attr=0):
        if name:
            self.name = name
            self.kind = data.kind
            self.data = data
            self.attr = attr

    @classmethod
    def read(cls, stream, index):
        self = cls()
        self.name = index.get_multiname(stream.read_u30())
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

        if self.attr & self.ATTR_Metadata: #metadata to be removed
            metadata_count = stream.read_u30()
            self.metadata = [index.get_metadata(stream.read_u30())
                for i in range(metadata_count)]
        return self

    def write(self, stream, index):
        stream.write_u30(index.get_multiname_index(self.name))
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

    def __repr__(self):
        return '<Trait {0}:{1} {2}>'.format(self.name, self.kind, self.data)

class TraitMethod(ABCStruct):
    kind = 1

    def __init__(self, method, disp_id=0):
        self.disp_id = disp_id
        self.method = method

    @classmethod
    def read(cls, stream, index):
        disp_id = stream.read_u30()
        return cls(index.get_method(stream.read_u30()), disp_id=disp_id)

    def write(self, stream, index):
        stream.write_u30(self.disp_id)
        stream.write_u30(index.get_method_index(self.method))

class TraitFunction(ABCStruct):
    kind = 5

    def __init__(self, function, disp_id=0):
        self.disp_id = disp_id
        assert isinstance(function, MethodInfo), function
        self.function = function

    @classmethod
    def read(cls, stream, index):
        disp_id = stream.read_u30()
        return cls(index.get_method(stream.read_u30()), disp_id=disp_id)

    def write(self, stream, index):
        stream.write_u30(self.disp_id)
        stream.write_u30(index.get_method_index(self.function))

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
            bcode = bytecode.parse(self.code, mindex)
        ext_labels = defaultdict(list)
        for exc in self.exception_info:
            for (k, v) in exc.put_labels(bcode):
                ext_labels[k].append(v)
        self.bytecode = list(map(itemgetter(1),
            bytecode.make_labels(bcode, ext_labels)))
        return self

    def write(self, stream, index):
        with index.for_method(self) as mindex:
            bcode, self.code = bytecode.assemble(self.bytecode, mindex)
        if not isinstance(stream, DummyABCStream):
            lindex = dict((label, index)
                for (index, label) in bcode
                if isinstance(label, bytecode.Label))
            for exc in self.exception_info:
                exc.get_labels(lindex)
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

    def put_labels(self, bytecodes):
        p = self.exc_from, bytecode.Label()
        self.exc_from = p[1]
        yield p
        p = self.exc_to, bytecode.Label()
        self.exc_to = p[1]
        yield p
        p = self.target, bytecode.Label()
        self.target = p[1]
        yield p

    def write(self, stream, index):
        stream.write_u30(self.exc_from)
        stream.write_u30(self.exc_to)
        stream.write_u30(self.target)
        stream.write_u30(index.get_multiname_index(self.exc_type))
        if self.var_name:
            stream.write_u30(index.get_multiname_index(self.var_name))
        else:
            stream.write_u30(0)

    def get_labels(self, alllabels):
        self.exc_from = alllabels[self.exc_from]
        self.exc_to = alllabels[self.exc_to]
        self.target = alllabels[self.target]

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
    def read(cls, stream, index):
        kind = stream.read_u8()
        self = multiname_kinds[kind]._read(stream, index)
        assert kind == self.kind
        return self

class QName(MultinameInfo):
    kind = CONSTANT_QName

    def __init__(self, namespace, name):
        assert isinstance(namespace, NamespaceInfo), namespace
        assert isinstance(name, str), name
        self.namespace = namespace
        self.name = name

    @classmethod
    def _read(cls, stream, index):
        return cls(index.get_namespace(stream.read_u30()),
            index.get_string(stream.read_u30()))

    def __repr__(self):
        return '<{0} {1}:{2}>'.format(self.__class__.__name__,
            self.namespace, self.name)

    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_namespace_index(self.namespace))
        stream.write_u30(index.get_string_index(self.name))

    def __eq__(self, other):
        return self.kind == other.kind \
            and self.name == other.name and self.namespace == other.namespace

    def __hash__(self):
        return hash((self.name, self.namespace))

class QNameA(QName):
    kind = CONSTANT_QNameA
class RTQName(MultinameInfo):
    kind = CONSTANT_RTQName
    @classmethod
    def _read(cls, stream, index):
        self = cls()
        self.name = index.get_string(stream.read_u30())
        return self
    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.name)
    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_string_index(self.name))
class RTQNameA(RTQName):
    kind = CONSTANT_RTQNameA
class RTQNameL(MultinameInfo):
    kind = CONSTANT_RTQNameL
    @classmethod
    def _read(cls, stream, index):
        self = cls()
        return self
    def __repr__(self):
        return '<RTQNameL>'
    def write(self, stream, index):
        stream.write_u8(self.kind)
class RTQNameLA(RTQNameL):
    kind = CONSTANT_RTQNameLA
class Multiname(MultinameInfo):
    kind = CONSTANT_Multiname
    @classmethod
    def _read(cls, stream, index):
        self = cls()
        self.name = index.get_string(stream.read_u30())
        self.namespace_set = index.get_namespace_set(stream.read_u30())
        return self
    def __repr__(self):
        return '<{0} {1}:{2}>'.format(self.__class__.__name__,
            self.namespace_set, self.name)
    def write(self, stream, index):
        stream.write_u8(self.kind)
        stream.write_u30(index.get_namespace_set_index(self.namespace_set))
        stream.write_u30(index.get_string_index(self.name))
class MultinameA(Multiname):
    kind = CONSTANT_MultinameA

class MultinameL(MultinameInfo):
    kind = CONSTANT_MultinameL

    def __init__(self, namespace_set):
        self.namespace_set = namespace_set

    @classmethod
    def _read(cls, stream, index):
        return cls(index.get_namespace_set(stream.read_u30()))

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.namespace_set)

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
        return '<InstanceInfo {0}({1})>'.format(self.name, self.super_name)

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
        return '<Class {0}({1})>'.format(self.instance_info.name,
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
        assert isinstance(value, str), "Value {0!r} is not string".format(value)
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
            #~ assert not val, 'Value {0} for CONSTANT_True'.format(val)
            return True
        elif kind == CONSTANT_False:
            #~ assert not val, 'Value {0} for CONSTANT_False'.format(val)
            return False
        elif kind == CONSTANT_Null:
            return None
        elif kind == CONSTANT_Undefined:
            return Undefined()
        elif kind in namespace_kinds:
            return self.get_namespace(val)
        else:
            raise NotImplementedError(kind)

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
        elif isinstance(value, uint):
            return CONSTANT_Uint, self.get_uinteger_index(value)
        elif isinstance(value, int):
            return CONSTANT_Int, self.get_integer_index(value)
        elif isinstance(value, str):
            return CONSTANT_Utf8, self.get_string_index(value)
        elif isinstance(value, NamespaceInfo):
            return value.kind, self.get_namespace_index(value)
        else:
            raise NotImplementedError(value)

    def __enter__(self):
        return self

    def __exit__(self, A, B, C):
        del self.cpool
        del self._method

class IndexCreator(object):
    def __init__(self, data):
        self.data = data
        self.strings = defaultdict(int)
        self.integers = defaultdict(int)
        self.uintegers = defaultdict(int)
        self.doubles = defaultdict(int)
        self.multinames = defaultdict(int)
        self.namespaces = defaultdict(int)
        self.namespace_sets = defaultdict(int)
        self.metadata = defaultdict(int)

    def update(self, data):
        data.constant_pool.integer = list(map(itemgetter(0),
            sorted(self.integers.items(), key=itemgetter(1))))
        data.constant_pool.double = list(map(itemgetter(0),
            sorted(self.doubles.items(), key=itemgetter(1))))
        data.constant_pool.string = list(map(itemgetter(0),
            sorted(self.strings.items(), key=itemgetter(1))))
        data.constant_pool.multiname_info = list(map(itemgetter(0),
            sorted(self.multinames.items(), key=itemgetter(1))))
        data.constant_pool.namespace_info = list(map(itemgetter(0),
            sorted(self.namespaces.items(), key=itemgetter(1))))
        data.constant_pool.ns_set_info = list(map(itemgetter(0),
            sorted(self.namespace_sets.items(), key=itemgetter(1))))
        data.metadata_info = list(map(itemgetter(0),
            sorted(self.metadata.items(), key=itemgetter(1))))

    def get_string_index(self, value):
        assert isinstance(value, str), "Value {0!r} is not string".format(value)
        self.strings[value] += 1
        return 0

    def get_integer_index(self, value):
        self.integers[value] += 1
        return 0

    def get_uinteger_index(self, value):
        self.uintegers[value] += 1
        return 0

    def get_multiname_index(self, value):
        if isinstance(value, AnyType):
            return 0
        self.multinames[value] += 1
        value.write(DummyABCStream(), self)
        return 0

    def get_namespace_index(self, value):
        self.namespaces[value] += 1
        value.write(DummyABCStream(), self)
        return 0

    def get_namespace_set_index(self, value):
        self.namespace_sets[value] += 1
        value.write(DummyABCStream(), self)
        return 0

    def get_double_index(self, value):
        self.doubles[value] += 1
        return 0

    def get_method_index(self, meth):
        return self.data.method_info.index(meth)

    def get_class_index(self, cls):
        return self.data.class_info.index(cls)

    def get_metadata_index(self, value):
        self.metadata[value] += 1
        return 0

    def for_method(self, method):
        self._method = method
        return self

    def get_exception_info(self, index):
        return self._method.exception_info[index]

    def get_exception_info_index(self, value):
        return self._method.exception_info.index(value)

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
        elif isinstance(value, uint):
            return CONSTANT_Uint, self.get_uinteger_index(value)
        elif isinstance(value, int):
            return CONSTANT_Int, self.get_integer_index(value)
        elif isinstance(value, str):
            return CONSTANT_Utf8, self.get_string_index(value)
        else:
            return value.kind, self.get_namespace_index(value)

    def __enter__(self):
        assert self._method
        return self

    def __exit__(self, A, B, C):
        del self._method

class ABCFile(ABCStruct):

    def __init__(self):
        self.minor_version = 16
        self.major_version = 46
        self.constant_pool = CPoolInfo()
        self.method_info = []
        self.metadata_info = []
        self.class_info = []
        self.script_info = []
        self.method_body_info = []

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
        index = IndexCreator(self)
        self._write(DummyABCStream(), index)
        index.update(self)
        self._write(stream, Index(self))

    def _write(self, stream, index):
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
        self._decode()

    def parse_body(self):
        self.flags = struct.unpack('<L', self.data[:4])[0]
        idx = self.data.index(b'\x00', 4)
        self.name = self.data[4:idx].decode('utf-8')
        self.body = self.data[idx+1:]

    def _decode(self):
        abc = ABCStream(self.body)
        self.real_body = ABCFile.read(abc)

    def disassemble(self):
        for body in self.real_body.method_body_info:
            print("METHOD", body.method.name, "PARAMS",
                getattr(body.method, 'param_name', body.method.param_type))
            index = Index(self.real_body, body)
            for (off, code) in bytecode.parse(body.code, index):
                print('    {0:5d} {1!s}'.format(off, code))

    def empty(self):
        self.real_body = ABCFile()

    def clean_metadata(self):
        self.real_body.metadata_info[:] = []
        for i in self.real_body.method_info:
            if hasattr(i, 'param_name'):
                del i.param_name
        for s in self.real_body.method_body_info:
            for t in s.traits_info:
                if hasattr(t, 'metadata'):
                    del t.metadata
        for s in self.real_body.script_info:
            for t in s.traits_info:
                if hasattr(t, 'metadata'):
                    del t.metadata
        for s in self.real_body.class_info:
            for t in s.trait:
                if hasattr(t, 'metadata'):
                    del t.metadata
            for t in s.instance_info.trait:
                if hasattr(t, 'metadata'):
                    del t.metadata

    def blob(self):
        buf = ABCStream()
        prefix = struct.pack('<L', self.flags)+self.name.encode('utf-8')+b'\x00'
        self.real_body.write(buf)
        self.data = prefix + buf.getvalue()
        self.length = len(self.data)
        return super().blob()

from . import bytecode
