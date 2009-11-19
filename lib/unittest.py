
@package('unittest')
class Failure(Error):
    def __init__(self, message):
        super().__init__()
        self.message = message

@package('unittest')
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

@package('unittest')
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
