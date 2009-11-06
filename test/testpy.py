from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat
from flash.display import StageAlign
from flash.events import Event
from flash.utils import Dictionary

class Failure(Error):
    def __init__(self, message):
        super().__init__()
        self.message = message

class Test:
    """Base class for all tests"""
    def __init__(self, reporter, name):
        self.name = name
        self.reporter = reporter
    def assertTrue(self, val):
        self.reporter.add_assert()
        if not val:
            raise Failure("Assertion failed ``" + val + "'' is not True")
    def assertFalse(self, val):
        self.reporter.add_assert()
        if val:
            raise Failure("Assertion failed ``" + val + "'' is not False")
    def assertEquals(self, a, b):
        self.reporter.add_assert()
        if a != b:
            raise Failure("Assertion failed ``" + a + "'' != ``" + b + "''")
    def assertFloatEquals(self, a, b):
        self.reporter.add_assert()
        if -0.001 < a - b < 0.001:
            raise Failure("Assertion failed ``" + a + "'' != ``" + b + "''")
    def assertNotEquals(self, a, b):
        self.reporter.add_assert()
        if a == b:
            raise Failure("Assertion failed ``" + a + "'' == ``" + b + "''")
    def assertFloatNotEquals(self, a, b):
        self.reporter.add_assert()
        dif = a-b
        if dif > 0.001 or dif < -0.001:
            raise Failure("Assertion failed ``" + a + "'' != ``" + b + "''")
    def run(self):
        self.reporter.start(self.name)
        try:
            self.test()
        except Failure as f:
            self.reporter.fail(f)
        except Error as e:
            self.reporter.error(e)
        else:
            self.reporter.ok()

class Data(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testMakeList()
        self.testMakeDict()
        self.testUnpack()

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

class TestMath(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.operators()
        self.boolean()
        self.precedence()
        self.augmented_assign()

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

class Loops(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testRange1()
        self.testRange2()
        self.testRange3()
        self.testRange4()
        self.testRange5()
        self.testRange6()
        self.testWhile()
        self.testObjectIter()

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
    def __init__(self):
        pass

    def hello(self):
        return 'hello'

    def world(self):
        return self.hello() + ' baby'

class B(A):
    def __init__(self):
        super().__init__()

    def hello(self):
        return 'Hello!'

    def world(self):
        return super().world() + ' bear'

class TestClass(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.testOverride()

    def testOverride(self):
        self.assertEquals(A().hello(), 'hello')
        self.assertEquals(B().hello(), 'Hello!')
        a = A()
        self.assertEquals(a.hello(), 'hello')
        self.assertEquals(a.world(), 'hello baby')
        a = B()
        self.assertEquals(a.hello(), 'Hello!')
        self.assertEquals(a.world(), 'Hello! baby bear')

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

class Reporter:
    def __init__(self, textlabel):
        self.textlabel = textlabel
        self.number = 0
        self.successful = 0
        self.failed = 0
        self.assertions = 0
        self.at_start = False

    def start(self, name):
        self.number += 1
        self.at_start = True
        self.textlabel.appendText(name + '... ')

    def ok(self):
        if not self.at_start:
            self.textlabel.appendText('... ')
        self.textlabel.appendText('OK\n')
        self.successful += 1

    def fail(self, failure):
        if not self.at_start:
            self.textlabel.appendText('... ')
        self.debug(failure.getStackTrace())
        self.textlabel.appendText('Fail: '+failure.message+'\n')
        self.failed += 1

    def error(self, error):
        if not self.at_start:
            self.textlabel.appendText('... ')
        self.textlabel.appendText('Error: '+error.getStackTrace()+'\n')
        self.failed += 1

    def add_assert(self):
        self.assertions += 1

    def debug(self, val):
        if self.at_start:
            self.textlabel.appendText('\n')
            self.at_start = False
        self.textlabel.appendText('Debug: ' + val + '\n')

    def finish(self):
        self.textlabel.appendText("Tests run: " + self.number
            + ", successful: " + self.successful
            + ", failures: " + self.failed
            + ", assertions: " + self.assertions + "\n")

@package('')
class Main(Sprite):

    def __init__(self):
        super().__init__()
        self.init('world')

    def init(self, value):
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
        self.reporter.finish()
