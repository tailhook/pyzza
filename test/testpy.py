from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat
from flash.display import StageAlign
from flash.events import Event

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

class TestMath(Test):
    def __init__(self, reporter, name):
        super().__init__(reporter, name)

    def test(self):
        self.operators()
        self.precedence()
        self.augmented_assign()

    def operators(self):
        self.assertEquals(2*3, 6)
        self.assertEquals(2+3, 5)
        self.assertEquals(6/3, 2)
        self.assertEquals(7-3, 4)

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
        TestMath(self.reporter, 'Math').run()
        Loops(self.reporter, 'Loops').run()
        Exceptions(self.reporter, 'Exceptions').run()
        self.reporter.finish()
