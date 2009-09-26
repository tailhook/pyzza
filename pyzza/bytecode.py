from .io import ABCStream

def gather_bytecodes(name, bases, dic):
    res = {}
    for v in dic.values():
        if hasattr(v, 'code'):
            res[v.code] = v
    return res

class Bytecode(object):
    __slots__ = ()
    code = None

    @classmethod
    def read(cls, stream):
        res = cls()
        res._read(stream)
        return res

    def _read(self, stream):
        pass # no operands

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
        __slots__ = ('byte_value',)
        code = 0x24
        def _read(self, stream):
            self.byte_value = stream.read_u8()

    class pushstring(Bytecode):
        __slots__ = ('index',)
        code = 0x2c
        def _read(self, stream):
            self.index = stream.read_u8()
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

    class pushtrue(Bytecode):
        __slots__ = ()
        code = 0x26

    class multiply(Bytecode):
        __slots__ = ()
        code = 0xa2

    class add(Bytecode):
        __slots__ = ()
        code = 0xa0

    class pushscope(Bytecode):
        __slots__ = ()
        code = 0x30

    class popscope(Bytecode):
        __slots__ = ()
        code = 0x1d

    class construct(Bytecode):
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

    class not_(Bytecode):
        __slots__ = ()
        code = 0x96

    class newobject(Bytecode):
        __slots__ = ('arg_count',)
        code = 0x55
        def _read(self, stream):
            self.arg_count = stream.read_u30()

    class dxns(Bytecode):
        __slots__ = ('index',)
        code = 0x06
        def _read(self, stream):
            self.index = stream.read_u30()

class Parser(object):

    def __init__(self, str):
        self._stream = ABCStream(str)

    def parse(self):
        while True:
            try:
                code = self._stream.read_u8()
            except IndexError:
                break #no more characters
            yield bytecodes[code].read(self._stream)

def parse(code):
    return list(Parser(code).parse())
