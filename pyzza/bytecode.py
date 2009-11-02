from collections import defaultdict
import sys

from .io import ABCStream
from . import io
from .abc import (MultinameInfo, MethodInfo, ExceptionInfo,
    ClassInfo, NamespaceInfo, Offset, Register,
    Multiname, MultinameL, QName, RTQName, RTQNameL
    )

def gather_bytecodes(name, bases, dic):
    res = {}
    glob = globals()
    for (k, v) in dic.items():
        if hasattr(v, 'code'):
            res[v.code] = v
            glob[k] = v
    return res

class BytecodeMeta(type):
    def __new__(cls, name, bases, dic):
        if 'format' in dic:
            dic['__slots__'] = tuple(a[0] for a in dic['format'])
        elif '__slots__' not in dic:
            dic['__slots__'] = ()
        return super().__new__(cls, name, bases, dic)

class Bytecode(object, metaclass=BytecodeMeta):
    __slots__ = ()
    format = (
        # (human-readable name, type, constantpool dict or None, value format),
        #   value format is one of  io.u30, io.s24, io.u8
        )
    code = None
    stack_before = ()
    stack_after = ()

    def __init__(self, *args):
        if args:
            for (i, (name, _, _, _)) in enumerate(self.format):
                setattr(self, name, args[i])

    @classmethod
    def read(cls, stream, index):
        res = cls()
        res._read(stream, index)
        return res

    def _read(self, stream, index):
        for (name, typ, idx, format) in self.format:
            val = stream.read_formatted(format)
            if idx is not None:
                val = getattr(index, 'get_' + idx)(val)
            if not isinstance(val, typ):
                val = typ(val)
            setattr(self, name, val)

    def write(self, stream, index):
        stream.write_u8(self.code)
        self._write(stream, index)

    def _write(self, stream, index):
        for (name, typ, idx, format) in self.format:
            val = getattr(self, name)
            assert isinstance(val, typ), "Arg {!r} for {!s} is wrong: {!r}"\
                .format(name, self.__class__.__name__, val)
            if idx is not None:
                val = getattr(index, 'get_{}_index'.format(idx))(val)
            val = stream.write_formatted(format, val)

    def __repr__(self):
        return '<{}>'.format(str(self))

    def __str__(self):
        return self.__class__.__name__ + \
            ''.join(' '+repr(getattr(self, a)) for (a,_,_,_) in self.format)

class PropertyBytecode(Bytecode):
    propertyattr = 'property'
    def _stack_before(self):
        val = getattr(self, self.propertyattr)
        if isinstance(val, (Multiname, QName)):
            return ('obj',)
        elif isinstance(val, RTQName):
            return ('obj', 'namespace')
        elif isinstance(val, MultinameL):
            return ('obj', 'name')
        elif isinstance(val, RTQNameL):
            return ('obj', 'namespace', 'name')
        else:
            raise NotImplementedError(val)
    stack_before = property(_stack_before)

class BinaryBytecode(Bytecode):
    stack_before = ('value1', 'value2')
    stack_after = ('value3',)

class UnaryBytecode(Bytecode):
    stack_before = ('value',)
    stack_after = ('value',)

class DebugBytecode(Bytecode):
    pass

class JumpBytecode(Bytecode):
    format = (
        ('offset', Offset, None, io.s24),
        )

class Label(object): # pseudo-bytecode
    __slots__ = ('_verify_stack',)
    format = ()
    stack_before = ()
    stack_after = ()
    def write(self, stream, index):
        pass
    def __repr__(self):
        return '<{}:{:x}[{}]>'.format(self.__class__.__name__, id(self),
            getattr(self, '_verify_stack', '*'))

class bytecodes(metaclass=gather_bytecodes):

    class add(BinaryBytecode):
        code = 0xa0

    class add_i(BinaryBytecode):
        code = 0xc5

    class astype(UnaryBytecode):
        format = (
            ('type', MultinameInfo, 'multiname', io.u30),
            )
        code = 0x86

    class astypelate(Bytecode):
        format = (
            ('type', MultinameInfo, 'multiname', io.u30),
            )
        code = 0x87
        stack_before = ('value', 'klass')
        stack_after = ('value',)

    class bitand(BinaryBytecode):
        code = 0xa8

    class bitnot(UnaryBytecode):
        code = 0x97

    class bitor(BinaryBytecode):
        code = 0xa9

    class bitxor(BinaryBytecode):
        code = 0xaa

    class call(Bytecode):
        format = (
            ('arg_count', int, None, io.u30),
            )
        code = 0x41
        @property
        def stack_before(self):
            return ('function', 'receiver') + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class callmethod(Bytecode):
        format = (
            ('method', MethodInfo, 'methods', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x43
        @property
        def stack_before(self):
            return ('receiver',) + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class callproperty(PropertyBytecode):
        format = (
            ('method', MultinameInfo, 'multiname', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x46
        propertyattr = 'method'
        @property
        def stack_before(self):
            return super()._stack_before() + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class callproplex(PropertyBytecode):
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x4c
        propertyattr = 'method'
        @property
        def stack_before(self):
            return super()._stack_before() + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class callpropvoid(PropertyBytecode):
        format = (
            ('method', MultinameInfo, 'multiname', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x4f
        propertyattr = 'method'
        @property
        def stack_before(self):
            return super()._stack_before() + tuple('arg{}'.format(i)
                for i in range(self.arg_count))

    class callstatic(Bytecode):
        format = (
            ('method', MethodInfo, 'method', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x44
        @property
        def stack_before(self):
            return ('receiver',) + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class callsuper(PropertyBytecode):
        format = (
            ('method', MultinameInfo, 'multiname', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x45
        propertyattr = 'method'
        @property
        def stack_before(self):
            return super()._stack_before() + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class callsupervoid(PropertyBytecode):
        format = (
            ('method', MultinameInfo, 'multiname', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x4e
        propertyattr = 'method'
        @property
        def stack_before(self):
            return super()._stack_before() + tuple('arg{}'.format(i)
                for i in range(self.arg_count))

    class checkfilter(UnaryBytecode):
        code = 0x78

    class coerce(UnaryBytecode):
        format = (
            ('type', MultinameInfo, 'multiname', io.u30),
            )
        code = 0x80

    class coerce_a(UnaryBytecode):
        code = 0x82

    class coerce_s(UnaryBytecode):
        code = 0x85

    class construct(Bytecode):
        format = (
            ('arg_count', int, None, io.u30),
            )
        code = 0x42
        @property
        def stack_before(self):
            return ('object',) + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class constructprop(PropertyBytecode):
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            ('arg_count', int, None, io.u30),
            )
        code = 0x4a
        @property
        def stack_before(self):
            return super()._stack_before() + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ('value',)

    class constructsuper(Bytecode):
        format = (
            ('arg_count', int, None, io.u30),
            )
        code = 0x49
        @property
        def stack_before(self):
            return ('object',) + tuple('arg{}'.format(i)
                for i in range(self.arg_count))
        stack_after = ()

    class convert_b(UnaryBytecode):
        code = 0x76

    class convert_i(UnaryBytecode):
        code = 0x73

    class convert_d(UnaryBytecode):
        code = 0x75

    class convert_o(UnaryBytecode):
        code = 0x77

    class convert_u(UnaryBytecode):
        code = 0x74

    class convert_s(UnaryBytecode):
        code = 0x70

    class debug(DebugBytecode):
        code = 0xef
        format = (
            ('debug_type', int, None, io.u8),
            ('index', str, 'string', io.u30),
            ('reg', int, None, io.u8),
            ('extra', int, None, io.u30),
            )

    class debugfile(DebugBytecode):
        code = 0xf1
        format = (
            ('filename', str, 'string', io.u30),
            )

    class debugline(DebugBytecode):
        code = 0xf0
        format = (
            ('linenum', int, None, io.u30),
            )

    class declocal(Bytecode):
        code = 0x94
        format = (
            ('register', Register, None, io.u30),
            )

    class declocal_i(Bytecode):
        code = 0xc3
        format = (
            ('register', Register, None, io.u30),
            )

    class decrement(UnaryBytecode):
        code = 0x93

    class decrement_i(UnaryBytecode):
        code = 0xc1

    class deleteproperty(PropertyBytecode):
        code = 0x6a
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        propertyattr = 'property'
        stack_after = ('value',)

    class divide(BinaryBytecode):
        code = 0xa3

    class dup(Bytecode):
        code = 0x2a
        stack_before = ('value',)
        stack_after = ('value', 'value')

    class dxns(Bytecode):
        code = 0x06
        format = (
            ('namespace', str, 'string', io.u30),
            )

    class dxnslate(Bytecode):
        code = 0x07
        stack_before = ('namespace',)

    class equals(BinaryBytecode):
        code = 0xab

    class esc_xattr(UnaryBytecode):
        code = 0x72

    class exc_xelem(UnaryBytecode):
        code = 0x71

    class findproperty(PropertyBytecode):
        code = 0x5e
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        def _stack_before(self):
            return super()._stack_before()[1:]
        stack_after = ('obj',)


    class findpropstrict(PropertyBytecode):
        code = 0x5d
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        @property
        def stack_before(self):
            return super()._stack_before()[1:]
        stack_after = ('obj',)

    class getdescendants(PropertyBytecode):
        code = 0x59
        format = (
            ('name', str, 'string', io.u30),
            )
        stack_after = ('value',)

    class getglobalscope(Bytecode):
        code = 0x64
        stack_after = ('obj',)

    class getglobalslot(Bytecode):
        code = 0x6e
        format = (
            ('slotindex', int, None, io.u30),
            )
        stack_after = ('value',)

    class getlex(Bytecode):
        code = 0x60
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        stack_after = ('obj',)

    class getlocal(Bytecode):
        code = 0x62
        format = (
            ('register', Register, None, io.u30),
            )
        stack_after = ('value',)

    class getlocal_0(Bytecode):
        code = 0xd0
        stack_after = ('value',)

    class getlocal_1(Bytecode):
        code = 0xd1
        stack_after = ('value',)

    class getlocal_2(Bytecode):
        code = 0xd2
        stack_after = ('value',)

    class getlocal_3(Bytecode):
        code = 0xd3
        stack_after = ('value',)

    class getproperty(PropertyBytecode):
        code = 0x66
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        stack_after = ('value',)

    class getscopeobject(Bytecode):
        code = 0x65
        format = (
            ('index', int, None, io.u8),
            )
        stack_after = ('scope',)

    class getslot(Bytecode):
        code = 0x6c
        format = (
            ('slotindex', int, None, io.u30),
            )
        stack_before = ('obj',)
        stack_after = ('value',)

    class getsuper(PropertyBytecode):
        code = 0x04
        format = (
            ('classname', MultinameInfo, 'multiname', io.u30),
            )
        propertyattr = 'classname'

    class greaterequals(BinaryBytecode):
        code = 0xb0 #verified in unittests

    class greaterthan(BinaryBytecode):
        code = 0xaf #verified in unittests

    class hasnext(Bytecode):
        code = 0x1f
        stack_before = ('obj', 'cur_index')
        stack_after = ('next_index',)

    class hasnext2(Bytecode):
        code = 0x32
        format = (
            ('object_reg', Register, None, io.u30),
            ('index_reg', Register, None, io.u30),
            )
        stack_after = ('value',)

    class ifeq(JumpBytecode):
        code = 0x13
        stack_before = ('value1', 'value2')

    class iffalse(JumpBytecode):
        code = 0x12
        stack_before = ('value',)

    class ifge(JumpBytecode):
        code = 0x18
        stack_before = ('value1', 'value2')

    class ifgt(JumpBytecode):
        code = 0x17
        stack_before = ('value1', 'value2')

    class ifle(JumpBytecode):
        code = 0x16
        stack_before = ('value1', 'value2')

    class iflt(JumpBytecode):
        code = 0x15
        stack_before = ('value1', 'value2')

    class ifnge(JumpBytecode):
        code = 0x0f
        stack_before = ('value1', 'value2')

    class ifngt(JumpBytecode):
        code = 0x0e
        stack_before = ('value1', 'value2')

    class ifnle(JumpBytecode):
        code = 0x0d
        stack_before = ('value1', 'value2')

    class ifnlt(JumpBytecode):
        code = 0x0c
        stack_before = ('value1', 'value2')

    class ifne(JumpBytecode):
        code = 0x14
        stack_before = ('value1', 'value2')

    class ifstricteq(JumpBytecode):
        code = 0x19
        stack_before = ('value1', 'value2')

    class ifstrictne(JumpBytecode):
        code = 0x1a
        stack_before = ('value1', 'value2')

    class iftrue(JumpBytecode):
        code = 0x11
        stack_before = ('value', )

    class in_(BinaryBytecode):
        code = 0xb4

    class inclocal(Bytecode):
        code = 0x92
        format = (
            ('register', Register, None, io.u30),
            )

    class inclocal_i(Bytecode):
        code = 0xc2
        format = (
            ('register', Register, None, io.u30),
            )

    class increment(UnaryBytecode):
        code = 0x91

    class increment_i(UnaryBytecode):
        code = 0xc0

    class initproperty(PropertyBytecode):
        code = 0x68
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        def _stack_before(self):
            return super()._stack_before() + ('value',)

    class instanceof(BinaryBytecode):
        code = 0xb1

    class istype(Bytecode):
        code = 0xb2
        format = (
            ('typename', MultinameInfo, 'multiname', io.u30),
            )
        stack_before = ('value',)
        stack_after = ('result',)

    class istypelate(Bytecode):
        code = 0xb3
        stack_before = ('value', 'type')
        stack_after = ('result',)

    class jump(JumpBytecode):
        code = 0x10

    class kill(Bytecode):
        code = 0x08
        format = (
            ('register', Register, None, io.u30),
            )

    class label(Bytecode, Label):
        code = 0x09

    class lessequals(BinaryBytecode):
        code = 0xae

    class lessthan(BinaryBytecode):
        code = 0xad

    class lookupswitch(Bytecode):
        __slots__ = ('default_offset', 'case_offsets')
        code = 0x1b
        def _read(self, stream, index):
            self.default_offset = Offset(stream.read_s24())
            self.case_offsets = [stream.read_s24()
                for i in range(stream.read_u30())]
        def __repr__(self):
            return '<{} {} {}({})>'.format(self.__class__.__name__,
                self.default_offset, len(self.case_offsets),
                ','.join(map(str, self.case_offsets)))

    class lshift(BinaryBytecode):
        code = 0xa5

    class modulo(BinaryBytecode):
        code = 0xa4

    class multiply(BinaryBytecode):
        code = 0xa2

    class multiply_i(BinaryBytecode):
        code = 0xc7

    class negate(UnaryBytecode):
        code = 0x90

    class negate_i(UnaryBytecode):
        code = 0xc4

    class newactivation(Bytecode):
        code = 0x57
        stack_after = ('newactivation',)

    class newarray(Bytecode):
        code = 0x56
        format = (
            ('arg_count', int, None, io.u30),
            )
        @property
        def stack_before(self):
            return tuple('value{}'.format(i) for i in range(self.arg_count))
        stack_after = ('array',)

    class newcatch(Bytecode):
        code = 0x5a
        format = (
            ('exception', ExceptionInfo, 'exception_info', io.u30),
            )
        stack_after = ('catchvalue', 'catchscope',)

    class newclass(Bytecode):
        code = 0x58
        format = (
            ('klass', ClassInfo, 'class', io.u30),
            )
        stack_before = ('basescope', 'basetype')
        stack_after = ('newclass',)

    class newfunction(Bytecode):
        code = 0x40
        format = (
            ('function', MethodInfo, 'method', io.u30),
            )
        stack_after = ('function_obj',)

    class newobject(Bytecode):
        code = 0x55
        format = (
            ('arg_count', int, None, io.u30),
            )
        @property
        def stack_before(self):
            return sum(
                (('name{}'.format(i), 'value{}'.format(i))
                for i in range(self.arg_count)),
                tuple())
        stack_after = ('newobj',)

    class nextname(Bytecode):
        code = 0x1e
        stack_before = ('obj', 'index')
        stack_after = ('name',)

    class nextvalue(Bytecode):
        code = 0x23
        stack_before = ('obj', 'index')
        stack_after = ('value',)

    class nop(Bytecode):
        code = 0x02
    class nop1(Bytecode):
        code = 0xff

    class not_(Bytecode):
        code = 0x96

    class pop(Bytecode):
        code = 0x29
        stack_before = ('value',)

    class popscope(Bytecode):
        code = 0x1d

    class pushbyte(Bytecode):
        code = 0x24
        format = (
            ('byte_value', int, None, io.u8),
            )
        stack_after = ('value',)

    class pushdouble(Bytecode):
        code = 0x2f
        format = (
            ('double', float, 'double', io.u30),
            )
        stack_after = ('value',)

    class pushfalse(Bytecode):
        code = 0x27
        stack_after = ('value',)

    class pushint(Bytecode):
        code = 0x2d
        format = (
            ('integer', int, 'integer', io.u30),
            )
        stack_after = ('value',)

    class pushnamespace(Bytecode):
        code = 0x31
        format = (
            ('namespace', NamespaceInfo, 'namespace', io.u30),
            )
        stack_after = ('namespace',)

    class pushnan(Bytecode):
        code = 0x28
        stack_after = ('value',)

    class pushnull(Bytecode):
        code = 0x20
        stack_after = ('value',)

    class pushscope(Bytecode):
        code = 0x30
        stack_before = ('value',)

    class pushshort(Bytecode):
        code = 0x25
        format = (
            ('value', int, None, io.u30),
            )
        stack_after = ('value',)

    class pushstring(Bytecode):
        code = 0x2c
        format = (
            ('value', str, 'string', io.u30),
            )
        stack_after = ('value',)

    class pushtrue(Bytecode):
        code = 0x26
        stack_after = ('value',)

    class pushuint(Bytecode):
        code = 0x2e
        format = (
            ('value', int, 'uinteger', io.u30),
            )
        stack_after = ('value',)

    class pushundefined(Bytecode):
        code = 0x21
        stack_after = ('value',)

    class pushwith(Bytecode):
        code = 0x1c
        stack_before = ('scope_obj',)

    class returnvalue(Bytecode):
        code = 0x48
        stack_before = ('return_value',)

    class returnvoid(Bytecode):
        code = 0x47

    class rshift(BinaryBytecode):
        code = 0xa6

    class setlocal(Bytecode):
        code = 0x63
        format = (
            ('value', Register, None, io.u30),
            )
        stack_before = ('value',)

    class setlocal_0(Bytecode):
        code = 0xd4
        stack_before = ('value',)

    class setlocal_1(Bytecode):
        code = 0xd5
        stack_before = ('value',)

    class setlocal_2(Bytecode):
        code = 0xd6
        stack_before = ('value',)

    class setlocal_3(Bytecode):
        code = 0xd7
        stack_before = ('value',)

    class setglobalslot(Bytecode):
        code = 0x6f
        format = (
            ('slotindex', int, None, io.u30),
            )
        stack_before = ('value',)

    class setproperty(PropertyBytecode):
        code = 0x61
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        @property
        def stack_before(self):
            return super()._stack_before() + ('value',)

    class setslot(Bytecode):
        code = 0x6d
        format = (
            ('slotindex', int, None, io.u30),
            )
        stack_before = ('obj', 'value')

    class setsuper(PropertyBytecode):
        code = 0x05
        format = (
            ('property', MultinameInfo, 'multiname', io.u30),
            )
        def _stack_before(self):
            return super()._stack_before() + ('value',)

    class strictequals(BinaryBytecode):
        code = 0xac

    class subtract(BinaryBytecode):
        code = 0xa1

    class subtract_i(BinaryBytecode):
        code = 0xc6

    class swap(Bytecode):
        code = 0x2b
        stack_before = ('value1', 'value2')
        stack_after = ('value2', 'value1')

    class throw(Bytecode):
        code = 0x03
        stack_before = ('value',)

    class typeof(Bytecode):
        code = 0x95
        stack_before = ('value',)
        stack_after = ('typename',)

    class urshift(BinaryBytecode):
        code = 0xa7

class Parser(object):

    def __init__(self, str, index):
        self._stream = ABCStream(str)
        self._index = index

    def parse(self):
        while True:
            pos = self._stream.tell()
            try:
                code = self._stream.read_u8()
            except IndexError:
                break #no more characters
            code = bytecodes[code].read(self._stream, self._index)
            yield pos, code

class Assembler(object):

    def __init__(self, codes, index):
        self._codes = codes
        self._index = index

    def assemble(self):
        self._stream = ABCStream()
        codes = []
        memo = {}
        fwjumps = defaultdict(list)
        for code in self._codes:
            index = self._stream.tell()
            if isinstance(code, Label):
                memo[code] = Offset(index)
                fw = fwjumps.pop(code, None)
                if fw:
                    for i in fw:
                        self._stream.seek(i+1)
                        self._stream.write_s24(index-i-4)
                    self._stream.seek(index)
            elif isinstance(code, JumpBytecode):
                code = code.__class__(code.offset)
                if code.offset not in memo:
                    fwjumps[code.offset].append(index)
                    code.offset = Offset(0)
                else:
                    code.offset = Offset(memo[code.offset] - index - 4)
            code.write(self._stream, self._index)
            codes.append((index, code))
        assert not fwjumps, 'Not found forward jumps {!r}'.format(fwjumps)
        return codes, self._stream.getvalue()

def parse(code, index):
    return list(Parser(code, index).parse())

def assemble(codes, index):
    return Assembler(codes, index).assemble()

def _make_labels(codes, ext_labels):
    bw = {}
    labels = defaultdict(list, ((k, v[:])
        for (k, v) in ext_labels.items()))
    for (index, code) in codes:
        for i in labels.pop(index, ()):
            yield index, i
        if isinstance(code, JumpBytecode):
            code = code.__class__(code.offset)
            if code.offset < 0:
                code.offset = bw[index+4+code.offset]
            else:
                nlabel = Label()
                labels[index+4+code.offset].append(nlabel)
                code.offset = nlabel
        elif isinstance(code, label):
            bw[index] = code
        yield index, code
    if (index+1) in labels:
        print("WARNING: some labels after end of bytecodes", file=sys.stderr)
        for i in labels.pop(index+1, ()):
            yield index, i
    assert not labels, 'Not all labels put into stream {!r}'.format(labels)

def make_labels(codes, ext_labels=()):
    return list(_make_labels(codes, ext_labels))
