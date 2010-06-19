@package('string')
def repr(value):
    if isinstance(value, String):
        return '"'+value          \
            .replace('\\', r'\\') \
            .replace('"', r'\"')   \
            .replace('\r', r'\r') \
            .replace('\n', r'\n') \
            .replace('\t', r'\t') \
            +'"'
    elif isinstance(value, Number):
        return value.toString()
    elif isinstance(value, Boolean):
        return value.toString()
    elif isinstance(value, Array):
        return '[' + value.map(maprepr).join(', ') + ']'
    elif value == None:
        return 'null'
    elif value == undefined:
        return 'undefined'
    elif isinstance(value, Class):
        return value.toString()
    elif isinstance(value, Object):
        try:
            if value.__repr__:
                return value.__repr__()
        except ReferenceError: # for sealed (non-dynamic) classes
            pass
        if value.constructor != Object:
            return '<Instance of ' + value.constructor.toString() + '>'
        res = []
        for k, v in items(value):
            res.push(repr(k) + ': ' + repr(v))
        return '{' + res.join(', ') + '}'

def maprepr(value, i, j):
    return repr(value)

single_re = RegExp(r"\{\{|\}\}|\{([^}!:]*)(![^:}]+)?(:[^}]*)?\}", "g")
numformat_re = RegExp(r"^:([^}]?[<>=^])?(#?)([+]?)(\d*)(?:\.(\d+))?([bcdeEfFgGoxX%])$")
strformat_re = RegExp(r"^:([^}]?[<>^])?(\d*)(?:\.(\d+))?s?$")
number_re = RegExp(r"^-?\d+$")

@package('string')
@method
def format(pattern, *args):
    index = [0]
    def repl(str, field, convers, format, idx, pat):
        if str == '{{' or str == '}}':
            return str.charAt(0)
        if format:
            pass
        field = field.split('.')
        if not field[0]:
            field[0] = index[0]
            index[0] = index[0] + 1
        val = args
        for f in values(field):
            if number_re.test(f):
                val = val[Number(f)]
            else:
                if val == args:
                    val = args[0]
                val = val[f]
        if convers:
            if convers == '!s':
                val = String(val)
            elif convers == '!r':
                val = repr(val)
            else:
                raise Error("Wrong conversion " + repr(convers))
        try:
            if val.__format__:
                return val.__format__(format)
        except ReferenceError:
            pass
        except TypeError:
            pass
        return repr(val)
    return pattern.replace(single_re, repl)

digits = {
    'b': '01',
    'o': '01234567',
    'x': '0123456789abcdef',
    'X': '0123456789ABCDEF',
    }
prefixes = {
    'b': '0b',
    'o': '0o',
    'x': '0x',
    'X': '0x',
    }

@method
def number_format(self, fmt):
    if not fmt:
        return String(self)
    fmtparts = numformat_re.exec(fmt)
    if not fmtparts:
        raise Error("Wrong format specification " + repr(fmt))
    _, align, pref, plus, width, prec, fmt = fmtparts
    if self < 0:
        sig = '-'
        self = abs(self)
    elif plus:
        sig = '+'
    else:
        sig = ''
    prefix = ''
    if fmt == 'f':
        if prec:
            self = str(self.toFixed(float(prec)))
        else:
            self = str(self.toFixed(float(6)))
    elif fmt == 'd':
        self = str(Math.floor(abs(self)))
    elif digits[fmt]:
        res = ''
        dig = digits[fmt]
        base = dig.length
        while self:
            res = dig.charAt(self % base) + res
            self = Math.floor(self / base)
        if res:
            self = res
        else:
            self = '0'
        if pref:
            prefix = prefixes[fmt]
    elif fmt == 'c':
        self = String.fromCharCode(self)
    else:
        raise Error("Unimplemented format " + repr(fmt))
    if width:
        wid = Number(width)
        if self.length + sig.length + prefix.length < width:
            if Boolean(align) and align.length > 1:
                fillchar = align.charAt(0)
                align = align.charAt(1)
            else:
                fillchar = ' '
            if not align or align == '>':
                self = sig+prefix+self
                for i in range(wid - self.length):
                   self = fillchar + self
            elif align == '=':
                for i in range(wid - self.length - sig.length - prefix.length):
                   self = fillchar + self
                self = sig+prefix+self
            elif align == '<':
                self = sig+prefix+self
                for i in range(wid - self.length):
                   self += fillchar
            elif align == '^':
                self = sig+prefix+self
                for i in range((wid - self.length)/2):
                    self = fillchar + self + fillchar
                if self.length < wid:
                    self += fillchar
            else:
                raise Error("Wrong align " + repr(align))
            return self
    return sig+prefix+self

@method
def string_format(self, fmt):
    if not fmt:
        return self
    fmtparts = strformat_re.exec(fmt)
    if not fmtparts:
        raise Error("Wrong format specification " + repr(fmt))
    _, align, width, prec = fmtparts
    if prec:
        prec = Number(prec)
        if self.length > prec:
            self = self.substring(0, prec)
    if width:
        width = Number(width)
        if self.length < width:
            if Boolean(align) and align.length > 1:
                fillchar = align.charAt(0)
                align = align.charAt(1)
            else:
                fillchar = ' '
            if not align or align == '<':
                for i in range(width - self.length):
                   self += fillchar
            elif align == '>':
                for i in range(width - self.length):
                   self = fillchar + self
            elif align == '^':
                for i in range((width - self.length)/2):
                    self = fillchar + self + fillchar
                if self.length < width:
                    self += fillchar
            else:
                raise Error("Wrong align " + repr(align))
    return self

String.prototype.format = format
String.prototype.__format__ = string_format
Number.prototype.__format__ = number_format
