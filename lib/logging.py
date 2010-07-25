from string import repr

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

@package('logging')
class LogRecord:
    __slots__ = ('file', 'line', 'method', 'class_', 'level', 'message', 'args')
    def __init__(self, file, line, class_, method, level, message, args):
        self.file = file
        self.line = line
        self.method = method
        self.class_ = class_
        self.level = level
        self.message = message
        self.args = args

    def format(self):
        if self.args != None:
            self.message = self.message.format.apply(self.message, self.args)
            self.args = None
        return self.message

@package('logging')
class LogLevel:
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    name = {
        str(DEBUG): "DEBUG",
        str(INFO): "INFO",
        str(WARNING): "WARNING",
        str(ERROR): "ERROR",
        str(CRITICAL): "CRITICAL",
        }

    def __init__(self):
        pass

@package('logging')
class TraceHandler:
    def __init__(self, format="{1} at {file}:{line}: {2}"):
        self.format = format

    def log_record(self, rec):
        trace(self.format.format(rec, LogLevel.name[rec.level], rec.format()))


@package('logging')
class Log:

    def __init__(self):
        self.handlers = [TraceHandler()]

    def _log(self, rec):
        for handler in values(self.handlers):
            handler.log_record(rec)

    @staticmethod
    def add_handler(handler):
        log.handlers.push(handler)

    def clear_handlers(self):
        log.handlers = []

    @staticmethod
    @debuginfo("file", "line", "class", "method")
    @debuglevel("DEBUG")
    def debug(file, line, class_, method, message):
        log._log(LogRecord(file, line, class_, method, DEBUG, message, []))

    @staticmethod
    @debuginfo("file", "line", "class", "method")
    @debuglevel("INFO")
    def info(file, line, class_, method, message):
        log._log(LogRecord(file, line, class_, method, INFO, message, []))

    @staticmethod
    @debuginfo("file", "line", "class", "method")
    @debuglevel("WARNING")
    def warning(file, line, class_, method, message):
        log._log(LogRecord(file, line, class_, method, WARNING, message, []))

    @staticmethod
    @debuginfo("file", "line", "class", "method")
    @debuglevel("ERROR")
    def error(file, line, class_, method, message):
        log._log(LogRecord(file, line, class_, method, ERROR, message, []))

    @staticmethod
    @debuginfo("file", "line", "class", "method")
    @debuglevel("CRITICAL")
    def critical(file, line, class_, method, message):
        log._log(LogRecord(file, line, class_, method, CRITICAL, message, []))

log = Log()
