from .io import ABCStream

def gather_bytecodes(name, bases, dic):
    res = {}
    glob = globals()
    for (k, v) in dic.items():
        if hasattr(v, 'code'):
            res[v.code] = v
            glob[k] = v
    return res

class Bytecode(object):
    __slots__ = ()
    code = None

    def __init__(self, *args):
        if args:
            for (i, name) in enumerate(self.__slots__):
                setattr(self, name, args[i])

    @classmethod
    def read(cls, stream):
        res = cls()
        res._read(stream)
        return res

    def _read(self, stream):
        pass # no operands

    def __repr__(self):
        return '<{}{}>'.format(self.__class__.__name__,
            ''.join(' '+str(getattr(self, a)) for a in self.__slots__))

    def raw_print(self, file=None):
        print('    ' + self.__class__.__name__,
            *(getattr(self, a) for a in self.__slots__))

    def print(self, constant_pool, file=None):
        return self.raw_print(file=file) # by default

class bytecodes(metaclass=gather_bytecodes):

    class debugfile(Bytecode):
        __slots__ = ('index',)
        code = 0xf1
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            print('    debugfile', cpool.string[self.index-1], file=file)

    class debug(Bytecode):
        __slots__ = ('debug_type', 'index', 'reg', 'extra')
        code = 0xef
        def _read(self, stream):
            self.debug_type = stream.read_u8()
            self.index = stream.read_u30()
            self.reg = stream.read_u8()
            self.extra = stream.read_u30()
        def print(self, cpool, file=None):
            if self.debug_type == 1:
                print('    debug reg', cpool.string[self.index-1]
                    + '=' + str(self.reg+1), self.extra, file=file)
            else:
                self.raw_print(file=file)

    class debugline(Bytecode):
        __slots__ = ('linenum',)
        code = 0xf0
        def _read(self, stream):
            self.linenum = stream.read_u30()

    class pushbyte(Bytecode):
        __slots__ = ('value',)
        code = 0x24
        def _read(self, stream):
            self.value = stream.read_u8()

    class pushshort(Bytecode):
        __slots__ = ('value',)
        code = 0x25
        def _read(self, stream):
            self.value = stream.read_u30()

    class pushint(Bytecode):
        __slots__ = ('index',)
        code = 0x2d
        def _read(self, stream):
            self.index = stream.read_u30()

    class pushdouble(Bytecode):
        __slots__ = ('index',)
        code = 0x2f
        def _read(self, stream):
            self.index = stream.read_u30()

    class pushstring(Bytecode):
        __slots__ = ('index',)
        code = 0x2c
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            str = cpool.string[self.index-1]
            print('    pushstring', repr(str), file=file)

    class returnvalue(Bytecode):
        __slots__ = ()
        code = 0x48

    class returnvoid(Bytecode):
        __slots__ = ()
        code = 0x47

    class coerce_a(Bytecode):
        __slots__ = ()
        code = 0x82

    class coerce_s(Bytecode):
        __slots__ = ()
        code = 0x85

    class coerce(Bytecode):
        __slots__ = ('index',)
        code = 0x80
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    coerce', mn.repr(cpool), file=file)

    class convert_s(Bytecode):
        __slots__ = ()
        code = 0x70

    class convert_i(Bytecode):
        __slots__ = ()
        code = 0x73

    class convert_u(Bytecode):
        __slots__ = ()
        code = 0x74

    class convert_d(Bytecode):
        __slots__ = ()
        code = 0x75

    class convert_b(Bytecode):
        __slots__ = ()
        code = 0x76

    class convert_o(Bytecode):
        __slots__ = ()
        code = 0x77

    class nextname(Bytecode):
        __slots__ = ()
        code = 0x1e

    class istypelate(Bytecode):
        __slots__ = ()
        code = 0xb3

    class equals(Bytecode):
        __slots__ = ()
        code = 0xab

    class strictequals(Bytecode):
        __slots__ = ()
        code = 0xac

    class lessthan(Bytecode):
        __slots__ = ()
        code = 0xad

    class lessequals(Bytecode):
        __slots__ = ()
        code = 0xae

    class greaterthan(Bytecode):
        __slots__ = ()
        code = 0xaf

    class greaterequals(Bytecode):
        __slots__ = ()
        code = 0xb0

    class dup(Bytecode):
        __slots__ = ()
        code = 0x2a

    class kill(Bytecode):
        __slots__ = ('index',)
        code = 0x08
        def _read(self, stream):
            self.index = stream.read_u8()
        def print(self, cpool, file=None):
            print('    kill', self.index, file=file)

    class setlocal_0(Bytecode):
        __slots__ = ()
        code = 0xd4

    class setlocal_1(Bytecode):
        __slots__ = ()
        code = 0xd5

    class setlocal_2(Bytecode):
        __slots__ = ()
        code = 0xd6

    class setlocal_3(Bytecode):
        __slots__ = ()
        code = 0xd7

    class setlocal(Bytecode):
        __slots__ = ('index',)
        code = 0x63
        def _read(self, stream):
            self.index = stream.read_u30()

    class getlocal_0(Bytecode):
        __slots__ = ()
        code = 0xd0

    class getlocal_1(Bytecode):
        __slots__ = ()
        code = 0xd1

    class getlocal_2(Bytecode):
        __slots__ = ()
        code = 0xd2

    class getlocal_3(Bytecode):
        __slots__ = ()
        code = 0xd3

    class getlocal(Bytecode):
        __slots__ = ('index',)
        code = 0x62
        def _read(self, stream):
            self.index = stream.read_u30()

    class pushfalse(Bytecode):
        __slots__ = ()
        code = 0x27

    class pushtrue(Bytecode):
        __slots__ = ()
        code = 0x26

    class pushundefined(Bytecode):
        __slots__ = ()
        code = 0x21

    class pushnan(Bytecode):
        __slots__ = ()
        code = 0x28

    class pop(Bytecode):
        __slots__ = ()
        code = 0x29

    class newactivation(Bytecode):
        __slots__ = ()
        code = 0x57

    class hasnext2(Bytecode):
        __slots__ = ('object_reg', 'index_reg')
        code = 0x32
        def _read(self, stream):
            self.object_reg = stream.read_u30()
            self.index_reg = stream.read_u30()

    class multiply(Bytecode):
        __slots__ = ()
        code = 0xa2

    class divide(Bytecode):
        __slots__ = ()
        code = 0xa3

    class negate(Bytecode):
        __slots__ = ()
        code = 0x90

    class add(Bytecode):
        __slots__ = ()
        code = 0xa0

    class subtract(Bytecode):
        __slots__ = ()
        code = 0xa1

    class rshift(Bytecode):
        __slots__ = ()
        code = 0xa6

    class bitnot(Bytecode):
        __slots__ = ()
        code = 0x97

    class bitand(Bytecode):
        __slots__ = ()
        code = 0xa8

    class bitor(Bytecode):
        __slots__ = ()
        code = 0xa9

    class bitxor(Bytecode):
        __slots__ = ()
        code = 0xaa

    class lshift(Bytecode):
        __slots__ = ()
        code = 0xa5

    class modulo(Bytecode):
        __slots__ = ()
        code = 0xa4

    class swap(Bytecode):
        __slots__ = ()
        code = 0x2b

    class typeof(Bytecode):
        __slots__ = ()
        code = 0x95

    class in_(Bytecode):
        __slots__ = ()
        code = 0xb4

    class increment(Bytecode):
        __slots__ = ()
        code = 0x91

    class decrement(Bytecode):
        __slots__ = ()
        code = 0x93

    class increment_i(Bytecode):
        __slots__ = ()
        code = 0xc0

    class pushscope(Bytecode):
        __slots__ = ()
        code = 0x30

    class popscope(Bytecode):
        __slots__ = ()
        code = 0x1d

    class getglobalscope(Bytecode):
        __slots__ = ()
        code = 0x64

    class nextvalue(Bytecode):
        __slots__ = ()
        code = 0x23

    class throw(Bytecode):
        __slots__ = ()
        code = 0x3

    class construct(Bytecode):
        __slots__ = ('arg_count',)
        code = 0x42
        def _read(self, stream):
            self.arg_count = stream.read_u30()

    class constructsuper(Bytecode):
        __slots__ = ('arg_count',)
        code = 0x49
        def _read(self, stream):
            self.arg_count = stream.read_u30()

    class constructprop(Bytecode):
        __slots__ = ('index', 'arg_count')
        code = 0x4a
        def _read(self, stream):
            self.index = stream.read_u30()
            self.arg_count = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    constructprop', mn.repr(cpool), self.arg_count, file=file)

    class findpropstrict(Bytecode):
        __slots__ = ('index',)
        code = 0x5d
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    findpropstrict', mn.repr(cpool), file=file)

    class callproperty(Bytecode):
        __slots__ = ('index', 'arg_count')
        code = 0x4f
        def _read(self, stream):
            self.index = stream.read_u30()
            self.arg_count = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    callproperty', mn.repr(cpool), self.arg_count, file=file)

    class getscopeobject(Bytecode):
        __slots__ = ('index',)
        code = 0x65
        def _read(self, stream):
            self.index = stream.read_u30()

    class getlex(Bytecode):
        __slots__ = ('index',)
        code = 0x60
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    getlex', mn.repr(cpool), file=file)

    class newclass(Bytecode):
        __slots__ = ('index',)
        code = 0x58
        def _read(self, stream):
            self.index = stream.read_u30()

    class getslot(Bytecode):
        __slots__ = ('slotindex',)
        code = 0x6c
        def _read(self, stream):
            self.slotindex = stream.read_u30()

    class setslot(Bytecode):
        __slots__ = ('slotindex',)
        code = 0x6d
        def _read(self, stream):
            self.slotindex = stream.read_u30()

    class getsuper(Bytecode):
        __slots__ = ('index',)
        code = 0x04
        def _read(self, stream):
            self.index = stream.read_u30()

    class setsuper(Bytecode):
        __slots__ = ('index',)
        code = 0x05
        def _read(self, stream):
            self.index = stream.read_u30()

    class callsuper(Bytecode):
        __slots__ = ('index', 'arg_count')
        code = 0x45
        def _read(self, stream):
            self.index = stream.read_u30()
            self.arg_count = stream.read_u30()

    class initproperty(Bytecode):
        __slots__ = ('index',)
        code = 0x68
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    initproperty', mn.repr(cpool), file=file)

    class getproperty(Bytecode):
        __slots__ = ('index',)
        code = 0x66
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    getproperty', mn.repr(cpool), file=file)

    class setproperty(Bytecode):
        __slots__ = ('index',)
        code = 0x61
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    setproperty', mn.repr(cpool), file=file)

    class deleteproperty(Bytecode):
        __slots__ = ('index',)
        code = 0x6a
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    deleteproperty', mn.repr(cpool), file=file)

    class findproperty(Bytecode):
        __slots__ = ('index',)
        code = 0x5e
        def _read(self, stream):
            self.index = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    findproperty', mn.repr(cpool), file=file)

    class callproperty(Bytecode):
        __slots__ = ('index', 'arg_count')
        code = 0x46
        def _read(self, stream):
            self.index = stream.read_u30()
            self.arg_count = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    callproperty', mn.repr(cpool), self.arg_count, file=file)

    class callpropvoid(Bytecode):
        __slots__ = ('index', 'arg_count')
        code = 0x4f
        def _read(self, stream):
            self.index = stream.read_u30()
            self.arg_count = stream.read_u30()
        def print(self, cpool, file=None):
            mn = cpool.multiname_info[self.index-1]
            print('    callpropvoid', mn.repr(cpool), self.arg_count, file=file)

    class newfunction(Bytecode):
        __slots__ = ('index',)
        code = 0x40
        def _read(self, stream):
            self.index = stream.read_u30()

    class inclocal_i(Bytecode):
        __slots__ = ('index',)
        code = 0xc2
        def _read(self, stream):
            self.index = stream.read_u30()

    class not_(Bytecode):
        __slots__ = ()
        code = 0x96

    class pushnull(Bytecode):
        __slots__ = ()
        code = 0x20

    class FAIL(Bytecode):
        __slots__ = ()
        code = 0xFF

    class jump(Bytecode):
        __slots__ = ('offset',)
        code = 0x10
        def _read(self, stream):
            self.offset = stream.read_s24()

    class lookupswitch(Bytecode):
        __slots__ = ('default_offset', 'case_count', 'case_offsets')
        code = 0x1b
        def _read(self, stream):
            self.default_offset = stream.read_s24()
            self.case_count = stream.read_u30()
            self.case_offsets = [stream.read_s24()
                for i in range(self.case_count)]

    class ifeq(Bytecode):
        __slots__ = ('offset',)
        code = 0x13
        def _read(self, stream):
            self.offset = stream.read_s24()

    class iffalse(Bytecode):
        __slots__ = ('offset',)
        code = 0x12
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifge(Bytecode):
        __slots__ = ('offset',)
        code = 0x18
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifgt(Bytecode):
        __slots__ = ('offset',)
        code = 0x17
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifle(Bytecode):
        __slots__ = ('offset',)
        code = 0x16
        def _read(self, stream):
            self.offset = stream.read_s24()

    class iflt(Bytecode):
        __slots__ = ('offset',)
        code = 0x15
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifnge(Bytecode):
        __slots__ = ('offset',)
        code = 0x0f
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifngt(Bytecode):
        __slots__ = ('offset',)
        code = 0x0e
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifnle(Bytecode):
        __slots__ = ('offset',)
        code = 0x0d
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifnlt(Bytecode):
        __slots__ = ('offset',)
        code = 0x0c
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifne(Bytecode):
        __slots__ = ('offset',)
        code = 0x14
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifstricteq(Bytecode):
        __slots__ = ('offset',)
        code = 0x19
        def _read(self, stream):
            self.offset = stream.read_s24()

    class ifstrictne(Bytecode):
        __slots__ = ('offset',)
        code = 0x1a
        def _read(self, stream):
            self.offset = stream.read_s24()

    class iftrue(Bytecode):
        __slots__ = ('offset',)
        code = 0x11
        def _read(self, stream):
            self.offset = stream.read_s24()

    class label(Bytecode):
        __slots__ = ()
        code = 0x09

    class newobject(Bytecode):
        __slots__ = ('arg_count',)
        code = 0x55
        def _read(self, stream):
            self.arg_count = stream.read_u30()

    class newarray(Bytecode):
        __slots__ = ('arg_count',)
        code = 0x56
        def _read(self, stream):
            self.arg_count = stream.read_u30()

    class newcatch(Bytecode):
        __slots__ = ('index',)
        code = 0x5a
        def _read(self, stream):
            self.index = stream.read_u30()

    class dxns(Bytecode):
        __slots__ = ('index',)
        code = 0x06
        def _read(self, stream):
            self.index = stream.read_u30()

    class getdescandants(Bytecode):
        __slots__ = ('index',)
        code = 0x59
        def _read(self, stream):
            self.index = stream.read_u30()

    class esc_xelem(Bytecode):
        __slots__ = ()
        code = 0x71

class Parser(object):

    def __init__(self, str):
        self._stream = ABCStream(str)

    def parse(self):
        while True:
            try:
                code = self._stream.read_u8()
            except IndexError:
                break #no more characters
            code = bytecodes[code].read(self._stream)
            yield code

def parse(code):
    return list(Parser(code).parse())
