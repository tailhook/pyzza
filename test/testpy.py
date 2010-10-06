from flash.display import DisplayObject, Sprite
from flash.text import TextField
from flash.text import TextFormat
from flash.display import StageAlign
from flash.events import Event
from flash.utils import Dictionary
from unittest import Test, Failure, Reporter
from string import repr, format

CONST1 = 11
CONST2 = 22

class Data(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testConst()
        self.testMakeList()
        self.testMakeDict()
        self.testUnpack()
        self.testInt()
        self.testType()

    def testConst(self):
        self.assertEquals(CONST1, 11)
        self.assertEquals(CONST2, 22)

    def testInt(self):
        self.assertEquals(0x10, 16) # byte
        self.assertEquals(2222, 0x8ae)
        self.assertEquals(Math.floor(2222 / 256), 0x8) # short
        self.assertEquals(0xFF0000, 16711680)
        self.assertEquals(0xFF0000 / 65536, 255) # 32bit, sorry
        self.assertEquals(0x870000 / 65536, 135)

    def testMakeList(self):
        a = [1, 2]
        self.assertEquals(a[0], 1)
        self.assertEquals(a[1], 2)
        self.assertEquals(a.length, 2)
        a = [True, False, 2.0]
        self.assertEquals(a[0], True)
        self.assertEquals(a[1], False)
        self.assertEquals(a[2], 2.0)
        self.assertEquals(a.length, 3)

    def testMakeDict(self):
        b = {'ab': 1, 'cd': 2}
        self.assertEquals(b['ab'], 1)
        self.assertEquals(b['cd'], 2)
        a = 'test'
        b = {a+'ab': 10/2, a+'cd': 6*3, 'str': 'test'}
        self.assertEquals(b['testab'], 5)
        self.assertEquals(b['testcd'], 18)
        self.assertEquals(b['str'], 'test')
        c = {}
        self.assertEquals(c['test'], undefined)
        c['test'] = 2
        self.assertEquals(c['test'], 2)
        c.test = 3
        self.assertEquals(c['test'], 3)
        self.assertEquals(c.test, 3)
        del c.test
        self.assertEquals(c.test, undefined)
        del a, b, c.test
        self.assertEquals(a, undefined)

    def repr(self, val):
        res = []
        for a, b in items(val):
            res.push(a + ': ' + b)
        return '{' + res.join(',') + '}'

    def testUnpack(self):
        a, b = [1,2]
        self.assertEquals(a, 1)
        self.assertEquals(b, 2)
        a = ["one", "two", "three"]
        a, b, c = a
        self.assertEquals(a, "one")
        self.assertEquals(b, "two")
        self.assertEquals(c, "three")
        a = {}
        b = {}
        c = {}
        a.val, b.val, c.val = ["one", "two", "three"]
        self.assertEquals(c.val, "three")
        self.assertEquals(b.val, "two")
        self.assertEquals(a.val, "one")

    def testType(self):
        self.assertTrue(isinstance("abc", String))
        s = String
        self.assertTrue(isinstance("abc", s))
        self.assertTrue(isinstance([], Array))
        self.assertTrue(isinstance([1, 2], Array))
        self.assertTrue(isinstance({}, Object))
        self.assertTrue(isinstance(Dictionary(), Dictionary))
        spr = Sprite()
        self.assertTrue(isinstance(spr, Sprite))
        self.assertTrue(isinstance(spr, DisplayObject))

class TestMath(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.operators()
        self.boolean()
        self.precedence()
        self.augmented_assign()
        self.builtins()

    def operators(self):
        self.assertEquals(2*3, 6)
        self.assertEquals(2+3, 5)
        self.assertEquals(6/3, 2)
        self.assertEquals(7-3, 4)
        self.assertFalse(3 > 5)
        self.assertTrue(3 > 1)
        self.assertFalse(3 > 3)
        self.assertTrue(999.3 > 999.0)
        self.assertTrue(2*2*2 < 3*3)
        self.assertTrue(11111111.0 < 22222222.0)
        self.assertFalse(311111111.0 < 22222222.0)
        self.assertTrue(1 <= 2)
        self.assertTrue(2 <= 2)
        self.assertFalse(2 <= 1)
        self.assertTrue(3 >= 2)
        self.assertTrue(2 >= 2)
        self.assertFalse(1 >= 2)

    def _reset(self):
        self.history = []

    def _true(self):
        self.history.push(True)
        return True

    def _false(self):
        self.history.push(False)
        return False

    def boolean(self):
        self.assertTrue(True and True)
        self.assertFalse(True and False)
        self.assertFalse(False and True)
        self.assertFalse(False and False)
        self.assertTrue(True or False)
        self.assertTrue(False or True)
        self.assertTrue(True or True)
        self.assertFalse(False or False)
        #testing short circuit
        self._reset()
        self.assertTrue(self._true() and self._true())
        self.assertEquals(self.history.length, 2)
        self._reset()
        self.assertFalse(self._true() and self._false())
        self.assertEquals(self.history.length, 2)
        self._reset()
        self.assertFalse(self._false() and self._true())
        self.assertEquals(self.history.length, 1)
        self._reset()
        self.assertFalse(self._false() and self._false())
        self.assertEquals(self.history.length, 1)
        self._reset()
        self.assertTrue(self._true() or self._false())
        self.assertEquals(self.history.length, 1)
        self._reset()
        self.assertTrue(self._false() or self._true())
        self.assertEquals(self.history.length, 2)
        self._reset()
        self.assertTrue(self._true() or self._true())
        self.assertEquals(self.history.length, 1)
        self._reset()
        self.assertFalse(self._false() or self._false())
        self.assertEquals(self.history.length, 2)

    def precedence(self):
        self.assertEquals(2*3+4, 10)
        self.assertEquals(4+2*3, 10)
        self.assertEquals(4+6/3, 6)
        self.assertEquals(6/3+4, 6)
        self.assertEquals(6/3-4, -2)
        self.assertEquals(4-6*3, -14)
        self.assertEquals(6*3-4, 14)
        self.assertEquals(6*(3-4), -6)

    def augmented_assign(self):
        i = 0
        self.assertEquals(i, 0)
        i += 2
        self.assertEquals(i, 2)
        i += i
        self.assertEquals(i, 4)
        i *= 3
        self.assertEquals(i, 12)
        i -= 2
        self.assertEquals(i, 10)
        i /= 2
        self.assertEquals(i, 5)
        j = 3
        i *= j
        self.assertEquals(i, 15)
        i %= 7
        self.assertEquals(i, 1)

    def builtins(self):
        # abs
        self.assertEquals(abs(-1), 1)
        self.assertEquals(abs(3), 3)
        a = 5
        self.assertEquals(abs(a+2), 7)
        self.assertEquals(abs(a-7), 2)
        # min
        self.assertEquals(min(5, 7), 5)
        self.assertEquals(min(4, -1), -1)
        self.assertEquals(min(-4, -1), -4)
        # max
        self.assertEquals(max(5, 7), 7)
        self.assertEquals(max(4, -1), 4)
        self.assertEquals(max(-4, -1), -1)

class Loops(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testTernary()
        self.testRange1()
        self.testRange2()
        self.testRange3()
        self.testRange4()
        self.testRange5()
        self.testRange6()
        self.testWhile()
        self.testNested()
        self.testObjectIter()
        self.mutable_iter()

    def testTernary(self):
        a = 1
        self.assertEquals((2 if a else 3), 2)
        self.assertEquals(7 if a else 8, 7)
        self.assertEquals(7 if not a else 8, 8)
        self.assertEquals(2 if not a else 3, 3)
        a = ''
        self.assertEquals(2 if a and 1 else 3, 3)

    def testRange1(self):
        j = 1.1
        for i in range(10):
            j += 1.1
        self.assertFloatEquals(j, 12.1)

    def testRange2(self):
        self.val = 0
        for i in range(10):
            self.val += 1
        self.assertEquals(self.val, 10)

    def testRange3(self):
        j = 7
        for i in range(11):
            j += 3
        self.assertEquals(j, 40)

    def testRange4(self):
        j = 0
        for i in range(11):
            if i > 3:
                break
        else:
            j = 1
        self.assertEquals(j, 0)
        j = 0
        for i in range(11):
            if i < 3:
                continue
            j += 1
        else:
            j += 100
        self.assertEquals(j, 108)

    def testRange5(self):
        j = 0
        for i in range(11):
            if i > 30:
                break
        else:
            j = 1
        self.assertEquals(j, 1)

    def testRange6(self):
        j = 0
        for i in range(1, 10):
            i += 5
            j += 1
        self.assertEquals(j, 9)
        j = 0
        for i in range(1, 10, 2):
            j += 1
        self.assertEquals(j, 5)
        j = 0
        a = 1
        b = 10
        c = 2
        for i in range(a, b, c):
            j += 1
        self.assertEquals(j, 5)
        j = 0
        for i in range(11, 1, -2):
            j += 1
        self.assertEquals(j, 5)
        j = 0
        a = 11
        b = 1
        c = -2
        for i in range(a, b, c):
            j += 1
        self.assertEquals(j, 5)

    def testWhile(self):
        i = 2
        j = 0
        while i < 21:
            i += 2
            j += 1
        self.assertEquals(i , 22)
        self.assertEquals(j, 10)
        while i < 32:
            i += 2
            j += 1
            if j > 25:
                break
        else:
            i = 100
        self.assertEquals(i , 100)
        self.assertEquals(j, 15)
        while i < 125:
            i += 2
            j += 1
            if j > 25:
                break
        else:
            i = 201
        self.assertEquals(i, 122)
        self.assertEquals(j, 26)

    def testNested(self):
        val = []
        for i in range(10):
            for j in range(5):
                val.push(i+j)
        self.assertEquals(val.length, 50)

    def testObjectIter(self):
        ob = {
            'key_a': 'aa',
            'key_b': 'bb',
            'key_c': 'cc',
            }
        j = 0
        for k in keys(ob):
            j += 1
            self.assertEquals(k.substr(0, 4), 'key_')
            self.assertTrue('abc'.indexOf(k.charAt(4)) >= 0)
            self.assertTrue(k.length == 5)
        self.assertEquals(j, 3)
        j = 0
        for v in values(ob):
            j += 1
            self.assertTrue('abc'.indexOf(v.charAt(0)) >= 0)
            self.assertTrue(v.charAt(0) == v.charAt(1))
            self.assertTrue(v.length == 2)
        self.assertEquals(j, 3)
        j = 0
        for k, v in items(ob):
            j += 1
            self.assertEquals(k.substr(0, 4), 'key_')
            self.assertTrue('abc'.indexOf(k.charAt(4)) >= 0)
            self.assertTrue(k.length == 5)
            self.assertTrue(k.charAt(4) == v.charAt(0))
            self.assertTrue('abc'.indexOf(v.charAt(0)) >= 0)
            self.assertTrue(v.charAt(0) == v.charAt(1))
            self.assertTrue(v.length == 2)
        self.assertEquals(j, 3)
        j = 0
        for k in values([7, 15, 23, 3]):
            self.assertTrue(k % 7 == j)
            j += 1
        self.assertEquals(j, 4)
        j = 0
        d = Dictionary()
        for k, v in values([[2, 12], [8, 3], [6, 4]]):
            j += 1
            self.assertEquals(k*v, 24)
            d[[k,v]] = k%v
        self.assertEquals(j, 3)
        j = 0
        for a, b in keys(d):
            j += 1
            self.assertEquals(k*v, 24)
        self.assertEquals(j, 3)
        j = 0
        for k, v in items(d):
            j += 1
            self.assertEquals(k[0]*k[1], 24)
            self.assertEquals(k[0]%k[1], v)
        self.assertEquals(j, 3)
        j = 0
        for (a, b), v in items(d):
            j += 1
            self.assertEquals(a*b, 24)
            self.assertEquals(a%b, v)
        self.assertEquals(j, 3)

    def mutable_iter(self):
        lst = [10, 20, 30]
        j = 0
        for v in values(lst):
            if v > 1:
                lst.push(v/2)
            j += 1
        self.assertEquals(j, 17)

class Exceptions(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testSimple()
        self.testNoMethod()
        self.testMethOk()
        self.testMethError()
        self.testArgError()
        self.testErrorSubclass()

    def testSimple(self):
        s = "None"
        try:
            raise "Hello"
        except String as e:
            s = e
        self.assertEquals(s, "Hello")

    def testNoMethod(self):
        s = "None"
        try:
            self.hello()
        except TypeError as e:
            s = e.getStackTrace()
        self.assertTrue(s.indexOf('hello is not a function') >= 0)
        self.assertTrue(s.indexOf('testNoMethod()') >= 0)

    def testTest(self):
        pass

    def testMethOk(self):
        try:
            self.testTest()
        except:
            a = 'Error'
        else:
            a = 'OK'
        self.assertEquals(a, 'OK')

    def testMethError(self):
        try:
            self.testTest(1, 2)
        except TypeError as e:
            a = 'TypeError'
        except:
            a = 'Error'
        else:
            a = 'OK'
        self.assertEquals(a, 'Error')

    def testArgError(self):
        try:
            self.testTest(1, 2)
        except TypeError as e:
            a = 'TypeError'
        except ArgumentError as e:
            a = 'ArgumentError'
        except:
            a = 'Error'
        else:
            a = 'OK'
        self.assertEquals(a, 'ArgumentError')

    def testErrorSubclass(self):
        try:
            self.testTest(1, 2)
        except TypeError as e:
            a = 'TypeError'
        except Error as e:
            a = 'ErrError'
        except:
            a = 'Error'
        else:
            a = 'OK'
        self.assertEquals(a, 'ErrError')

class A:
    STATIC1 = 1
    STATIC2 = 4
    def __init__(self):
        pass

    def hello(self):
        return 'hello'

    def world(self):
        return self.hello() + ' baby'

    @classmethod
    def get_static(cls):
        return cls.STATIC2

    @classmethod
    def say_hello(cls):
        return cls().hello()

    @staticmethod
    def say_hi():
        return 'hi'

class B(A):
    STATIC3 = 111
    def __init__(self):
        super().__init__()

    def hello(self):
        return 'Hello!'

    def world(self):
        return super().world() + ' bear'

class SlotA:
    __slots__ = ('a', 'b')
    def __init__(self, a, b):
        trace("A " + a + " B " + b)
        self.a = a
        self.b = b
        trace("A " + a + " B " + b + " A " + self.a + " B " + self.b)

class SlotB(SlotA):
    __slots__ = ('c', 'd')
    def __init__(self, c, d):
        super().__init__(c + d, c - d)
        self.c = c
        trace("C " + c + " D " + d + " A " + self.a + " B " + self.b)
        self.d = d

class SlotC(SlotA):
    __slots__ = ('c', '__dict__')
    def __init__(self, c, d):
        super().__init__(c + d, c - d)
        self.c = c
        self.d = d

@interface
class IAnimal:
    def __init__(self): pass
    def cry(self): pass
    def buy(self, name): pass
    def die(self): pass

class Dog(IAnimal):
    def __init__(self):
        pass

    def cry(self):
        return "Baw, waw"

    def buy(self, name):
        return "Dog's "+name

    def die(self):
        raise TypeError("Dog's can't die")

class Chicken(IAnimal):
    def __init__(self):
        pass

    def cry(self):
        return "Kud, kudah"

    def buy(self, name):
        return "Chicken's "+name

    def die(self):
        return 'rip'

class Parrot(A, IAnimal):
    def __init__(self):
        pass

    def cry(self):
        return "Popka durak"

    def buy(self, name):
        return "Parrot's "+name

    def die(self):
        return 'rip'

class TestClass(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testOverride()
        self.testStatic()
#~         self.testSlots()
        self.testClassmethods()
        self.testInterface()

    def testOverride(self):
        self.assertEquals(A().hello(), 'hello')
        self.assertEquals(B().hello(), 'Hello!')
        a = A()
        self.assertEquals(a.hello(), 'hello')
        self.assertEquals(a.world(), 'hello baby')
        a = B()
        self.assertEquals(a.hello(), 'Hello!')
        self.assertEquals(a.world(), 'Hello! baby bear')

    def testStatic(self):
        self.assertEquals(A.STATIC1, 1)
        self.assertEquals(A.STATIC2, 4)
        self.assertEquals(B.STATIC3, 111)
        # following works in python, but unfortunately not works in AVM
        # it would be great if somebody can find a way for this to work
        self.assertEquals(B.STATIC1, undefined)
        self.assertEquals(B.STATIC2, undefined)
        self.assertEquals(A().STATIC1, undefined)
        self.assertEquals(B().STATIC1, undefined)
        self.assertEquals(B().STATIC3, undefined)

    def testSlots(self):
        a = SlotA(2, 3)
        self.assertEquals(a.a, 2)
        self.assertEquals(a.b, 3)
        b = SlotB(7, 4)
        self.assertEquals(b.a, 11)
        self.assertEquals(b.b, 3)
        self.assertEquals(b.c, 7)
        self.assertEquals(b.d, 4)
        try:
            b.e = 'hello'
        except ReferenceError:
            pass
        else:
            raise Failure("ReferenceError not raised")
        c = SlotC(7, 4)
        c.e = 'hello'
        self.assertEquals(c.a, 11)
        self.assertEquals(c.b, 3)
        self.assertEquals(c.c, 7)
        self.assertEquals(c.d, 4)
        self.assertEquals(c.e, 'hello')

    def testClassmethods(self):
        self.assertEquals(A.get_static(), 4)
        self.assertEquals(A.say_hello(), 'hello')
        self.assertEquals(A.say_hi(), 'hi')
        try:
            B.say_hello()
        except TypeError:
            pass # sorry also for this error
        else:
            raise Failure("ReferenceError not raised")

    def testInterface(self):
        dog = Dog()
        self.assertEquals(dog.cry(), 'Baw, waw')
        self.assertEquals(dog.buy('food'), "Dog's food")
        try:
            dog.die()
        except TypeError:
            pass
        else:
            raise Failure("TypeError not raised")
        self.assertTrue(isinstance(dog, IAnimal))
        chick = Chicken()
        self.assertEquals(chick.cry(), 'Kud, kudah')
        self.assertEquals(chick.buy('food'), "Chicken's food")
        self.assertEquals(chick.die(), 'rip')
        self.assertTrue(isinstance(chick, IAnimal))
        parrot = Parrot()
        self.assertEquals(parrot.cry(), 'Popka durak')
        self.assertEquals(parrot.hello(), 'hello')
        self.assertTrue(isinstance(parrot, IAnimal))


def global_fun(a, b):
    return (a+b)*(a-b)

class Functions(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testFunction()
        self.testClosure()
        self.testVarArg()

    def testFunction(self):
        def test():
            return 'test'
        self.assertEquals(test(), 'test')
        def hello(name):
            return "Hello " + name
        self.assertEquals(hello("world"), 'Hello world')
        self.assertEquals(global_fun(4, 3), 7)
        def testdef(a=7):
            return a*3
        self.assertEquals(testdef(4), 12)
        self.assertEquals(testdef(), 21)

    def testClosure(self):
        a = 13
        b = 17
        def mply(c):
            return a*b*c
        self.assertEquals(mply(3), 13*17*3)
        b = 11
        self.assertEquals(mply(2), 13*11*2)
        def deep():
            def moredeep():
                return b
            return moredeep
        f = deep()
        self.assertEquals(f(), 11)
        def deep():
            b = 13
            def moredeep():
                return b
            return moredeep
        f = deep()
        self.assertEquals(f(), 13)
        self.assertEquals(deep()(), 13)
        def deep(b):
            def moredeep():
                return b
            return moredeep
        f = deep(88)
        self.assertEquals(f(), 88)
        self.assertEquals(deep(77)(), 77)
        def localfun():
            return deep(10)()
        self.assertEquals(localfun(), 10)
        for i in range(10):
            def hello():
                return i*2
            self.assertEquals(hello(), 2*i)
        try:
            hello(1)
        except ArgumentError as e:
            self.assertTrue(e.getStackTrace().indexOf('testpy.py') >= 0)
            def test():
                return e.getStackTrace()
            self.assertTrue(test().indexOf('testpy.py') >= 0)
        try:
            test()
        except TypeError:
            pass
        else:
            raise Failure("Exception was not cleared")

    def varmeth1(self, *args):
        return args

    def varmeth2(self, a, b, *args):
        self.assertEquals(a, b*b)
        return args

    def testVarArg(self):
        self.assertEquals(self.varmeth1().length, 0)
        ar = self.varmeth1(4, 6)
        self.assertEquals(ar.length, 2)
        self.assertEquals(ar[0]*ar[1], 24)
        self.assertEquals(self.varmeth2(4, 2).length, 0)
        ar = self.varmeth2(9, 3, 12, 2)
        self.assertEquals(ar.length, 2)
        self.assertEquals(ar[0]*ar[1], 24)
        this = self
        def prod(*args):
            res = 1
            for i in values(args):
                res *= i
            return res
        self.assertEquals(prod(), 1)
        self.assertEquals(prod(77), 77)
        self.assertEquals(prod(2, 3, 4), 24)

class Utility(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testRepr()
        self.testFormat()

    def testRepr(self):
        self.assertEquals(repr("test"), '"test"')
        self.assertEquals(repr("""Hello
World!"""), r'"Hello\nWorld!"')
        self.assertEquals(repr([1, 2, 3, "val"]), '[1, 2, 3, "val"]')
        v = repr({'a': 'b', 'c': 3})
        self.assertTrue(v == '{"a": "b", "c": 3}' or v == '{"c": 3, "a": "b"}')
        v = repr({'ar': [1,2], 'c': 3})
        self.assertTrue(v == '{"ar": [1, 2], "c": 3}'
            or v == '{"c": 3, "ar": [1, 2]}')
        self.assertEquals(repr(Failure("test")), '<Instance of [class Failure]>')

    def testFormat(self):
        self.assertEquals(''.format(), '')
        self.assertEquals('a'.format(), 'a')
        self.assertEquals('ab'.format(), 'ab')
        self.assertEquals('a{{'.format(), 'a{')
        self.assertEquals('a}}'.format(), 'a}')
        self.assertEquals('{{b'.format(), '{b')
        self.assertEquals('}}b'.format(), '}b')
        self.assertEquals('a{{b'.format(), 'a{b')

        # examples from the PEP:
        self.assertEquals("My name is {0}".format('Fred'), "My name is Fred")
        self.assertEquals("My name is {0.name}".format({'name': 'Fred'}),
                         "My name is Fred")
        self.assertEquals("My name is {0} :-{{}}".format('Fred'),
                         "My name is Fred :-{}")

        self.assertEquals(''.format(), '')
        self.assertEquals('abc'.format(), 'abc')
        self.assertEquals('{0}'.format('abc'), 'abc')
        self.assertEquals('{0:}'.format('abc'), 'abc')
#        self.assertEquals('{ 0 }'.format('abc'), 'abc')
        self.assertEquals('X{0}'.format('abc'), 'Xabc')
        self.assertEquals('{0}X'.format('abc'), 'abcX')
        self.assertEquals('X{0}Y'.format('abc'), 'XabcY')
        self.assertEquals('{1}'.format(1, 'abc'), 'abc')
        self.assertEquals('X{1}'.format(1, 'abc'), 'Xabc')
        self.assertEquals('{1}X'.format(1, 'abc'), 'abcX')
        self.assertEquals('X{1}Y'.format(1, 'abc'), 'XabcY')
        self.assertEquals('{0}'.format(-15), '-15')
        self.assertEquals('{0}{1}'.format(-15, 'abc'), '-15abc')
        self.assertEquals('{0}X{1}'.format(-15, 'abc'), '-15Xabc')
        self.assertEquals('{{'.format(), '{')
        self.assertEquals('}}'.format(), '}')
        self.assertEquals('{{}}'.format(), '{}')
        self.assertEquals('{{x}}'.format(), '{x}')
        self.assertEquals('{{{0}}}'.format(123), '{123}')
        self.assertEquals('{{{{0}}}}'.format(), '{{0}}')
        self.assertEquals('}}{{'.format(), '}{')
        self.assertEquals('}}x{{'.format(), '}x{')

        # weird field names
        self.assertEquals("{0.foo-bar}".format({'foo-bar':'baz'}), 'baz')
        self.assertEquals("{0.foo bar}".format({'foo bar':'baz'}), 'baz')
        self.assertEquals("{0. }".format({' ':3}), '3')


        self.assertEquals('{0.0}'.format(['abc', 'def']), 'abc')
        self.assertEquals('{0.1}'.format(['abc', 'def']), 'def')
        self.assertEquals('{0.1.0}'.format(['abc', ['def']]), 'def')

        # strings
        self.assertEquals('{0:.3s}'.format('abc'), 'abc')
        self.assertEquals('{0:.3s}'.format('ab'), 'ab')
        self.assertEquals('{0:.3s}'.format('abcdef'), 'abc')
        self.assertEquals('{0:.0s}'.format('abcdef'), '')
        self.assertEquals('{0:3.3s}'.format('abc'), 'abc')
        self.assertEquals('{0:2.3s}'.format('abc'), 'abc')
        self.assertEquals('{0:2.2s}'.format('abc'), 'ab')
        self.assertEquals('{0:3.2s}'.format('abc'), 'ab ')
        self.assertEquals('{0:x<0s}'.format('result'), 'result')
        self.assertEquals('{0:x<5s}'.format('result'), 'result')
        self.assertEquals('{0:x<6s}'.format('result'), 'result')
        self.assertEquals('{0:x<7s}'.format('result'), 'resultx')
        self.assertEquals('{0:x<8s}'.format('result'), 'resultxx')
        self.assertEquals('{0: <7s}'.format('result'), 'result ')
        self.assertEquals('{0:<7s}'.format('result'), 'result ')
        self.assertEquals('{0:>7s}'.format('result'), ' result')
        self.assertEquals('{0:>8s}'.format('result'), '  result')
        self.assertEquals('{0:^8s}'.format('result'), ' result ')
        self.assertEquals('{0:^9s}'.format('result'), ' result  ')
        self.assertEquals('{0:^10s}'.format('result'), '  result  ')
        self.assertEquals('{0:100}'.format('a'),
            'a                                                 '
            '                                                  ')
        self.assertEquals('{0:100}'.format(''),
            '                                                  '
            '                                                  ')

        # !r, !s and !a coercions
        self.assertEquals('{0!s}'.format('Hello'), 'Hello')
        self.assertEquals('{0!s:}'.format('Hello'), 'Hello')
        self.assertEquals('{0!s:15}'.format('Hello'), 'Hello          ')
        self.assertEquals('{0!s:15s}'.format('Hello'), 'Hello          ')
        self.assertEquals('{0!r}'.format('Hello'), '"Hello"')
        self.assertEquals('{0!r:}'.format('Hello'), '"Hello"')

        # test fallback to object.__format__
        self.assertEquals('{0}'.format({}), '{}')
        self.assertEquals('{0}'.format([]), '[]')
        self.assertEquals('{0}'.format([1]), '[1]')

        self.assertEquals('{:d}'.format(10), '10')
        self.assertEquals('{:0=5d}'.format(10), '00010')
        self.assertEquals('{: =5d}'.format(10), '   10')
        self.assertEquals('{:>5d}'.format(10), '   10')
        self.assertEquals('{:5d}'.format(10), '   10')
        self.assertEquals('{:<5d}'.format(10), '10   ')
        self.assertEquals('{:5d}'.format(100000), '100000')
        self.assertEquals('{:0=5d}'.format(-10), '-0010')
        self.assertEquals('{:>5d}'.format(-10), '  -10')
        self.assertEquals('{:<5d}'.format(-10), '-10  ')
        self.assertEquals('{:^5d}'.format(-10), ' -10 ')
        self.assertEquals('{:x^5d}'.format(-10), 'x-10x')
        self.assertEquals('{:x^5d}'.format(10), 'x10xx')
        self.assertEquals('{:x^+5d}'.format(10), 'x+10x')
        self.assertEquals('{:5d}'.format(-100000), '-100000')

        self.assertEquals('{:f}'.format(10.2), '10.200000')
        self.assertEquals('{:.2f}'.format(10.2), '10.20')
        self.assertEquals('{:.2f}'.format(10.222), '10.22')
        self.assertEquals('{:7.2f}'.format(10.222), '  10.22')
        self.assertEquals('{:+8.2f}'.format(10.222), '  +10.22')
        self.assertEquals('{:+8.2f}'.format(10.227), '  +10.23')

        self.assertEquals('{:x}'.format(0x1a), '1a')
        self.assertEquals('{:X}'.format(0x1a), '1A')
        self.assertEquals('{:o}'.format(0o12), '12')
        self.assertEquals('{:#o}'.format(0o12), '0o12')
        self.assertEquals('{:b}'.format(0b10101011100), '10101011100')
        self.assertEquals('{:#b}'.format(0b10101011100), '0b10101011100')
        self.assertEquals('{:#x}'.format(18), '0x12')
        self.assertEquals('{:>#5x}'.format(18), ' 0x12')
        self.assertEquals('{:0=#5x}'.format(18), '0x012')
        self.assertEquals('{:0=#5x}'.format(-18), '-0x12')
        self.assertEquals('{:#6x}'.format(-18), ' -0x12')

class Eval(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testEval()

    def testEval(self):

        @__eval__
        def test1(_):
            a = 1
            b = 3
            (a+b)*a

        @__eval__
        def test2(_):
            c = a+b
            c*2

        @__eval__
        def test3(_):
            def fun(arg):
                return arg*2
            fun(3)

        @__eval__
        def test4(_):
            fun(a+b)

        @__eval__
        def test5(_):
            def fun2():
                return _*2
            fun2()

        @__eval__
        def test6(_):
            fun2()

        @__eval__
        def test7(_):
            def fun3(c):
                return a+b+c

        @__eval__
        def test8(_):
            fun3(2)

        @__eval__
        def test9(_):
            def fun4(c):
                def fun(d):
                    return (a+b+c)*d
                return fun
            ff = fun4(10)
            ff(1)

        @__eval__
        def test10(_):
            [ff(2), ff(4), fun4(7)(2)]

        scope = {}
        val = test1.apply(scope, [val])
        self.assertEquals(val, 4)
        val = test2.apply(scope, [val])
        self.assertEquals(val, 8)
        val = test3.apply(scope, [val])
        self.assertEquals(val, 6)
        val = test4.apply(scope, [val])
        self.assertEquals(val, 8)
        val = test5.apply(scope, [val])
        self.assertEquals(val, 16)
        val = test6.apply(scope, [val])
        self.assertEquals(val, 32)
        val = test7.apply(scope, [val])
        self.assertEquals(val, undefined)
        val = test8.apply(scope, [val])
        self.assertEquals(val, 6)
        val = test9.apply(scope, [val])
        self.assertEquals(val, 14)
        val = test10.apply(scope, [val])
        self.assertEquals(repr(val), '[28, 56, 22]')
        self.assertEquals(scope.a, 1)
        self.assertEquals(scope.b, 3)
        self.assertEquals(scope.c, 4)
        self.assertEquals(scope._, 14)

@package('')
class Main(Sprite):

    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.stage.align = StageAlign.TOP_LEFT
        label = TextField()
        label.background = True
        label.border = True
        label.text = "Testing:\n"
        label.width = self.stage.stageWidth
        label.height = self.stage.stageHeight
        self.addChild(label)
        self.label = label
        self.reporter = Reporter(label)
        self.addEventListener(Event.ENTER_FRAME, self.start_tests)

    def start_tests(self, event):
        self.removeEventListener(Event.ENTER_FRAME, self.start_tests)
        Data(self.reporter, 'Data').run()
        TestMath(self.reporter, 'Math').run()
        Loops(self.reporter, 'Loops').run()
        Exceptions(self.reporter, 'Exceptions').run()
        TestClass(self.reporter, 'Classes').run()
        Functions(self.reporter, 'Functions').run()
        Utility(self.reporter, 'Utility').run()
        Eval(self.reporter, 'Eval').run()
        self.reporter.finish()
