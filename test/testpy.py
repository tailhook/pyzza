from flash.display import Sprite
from flash.text import TextField
from flash.text import TextFormat
from flash.display import StageAlign
from flash.events import Event

class Test:
    """Base class for all tests"""
    def __init__(self, reporter, name):
        self.name = name
        self.reporter = reporter
        self.result = True
    def assertTrue(self, val):
        self.reporter.add_assert()
        if not val:
            self.result = False
    def assertFalse(self, val):
        self.reporter.add_assert()
        if val:
            self.result = False
    def assertEquals(self, a, b):
        self.reporter.add_assert()
        if a != b:
            self.result = False
    def assertFloatEquals(self, a, b):
        self.reporter.add_assert()
        if -0.001 < a - b < 0.001:
            self.result = False
    def assertNotEquals(self, a, b):
        self.reporter.add_assert()
        if a == b:
            self.result = False
    def assertFloatNotEquals(self, a, b):
        self.reporter.add_assert()
        dif = a-b
        if dif > 0.001 or dif < -0.001:
            self.result = False
    def run(self):
        self.reporter.start(self.name)
        self.test()
        if self.result:
            self.reporter.ok()
        else:
            self.reporter.fail()

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

    def testSimple(self):
        s = "None"
        try:
            raise "Hello"
        except String as e:
            s = e
        self.assertEquals(s, "Hello")

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

    def fail(self):
        if not self.at_start:
            self.textlabel.appendText('... ')
        self.textlabel.appendText('Fail\n')
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
