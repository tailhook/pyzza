from lib2to3.pygram import driver
from lib2to3 import pygram, pytree
from lib2to3.pygram import token

from operator import attrgetter

from . import pretty

class Symbol(object):
    def __init__(self, grammar):
        for (k, v) in grammar.symbol2number.items():
            setattr(self, k, v)

import os.path
gfile = os.path.join(os.path.dirname(__file__), 'Grammar.txt')
grammar = driver.load_grammar(gfile)
symbol = Symbol(grammar)

class Node(object):
    __slots__ = ('lineno', 'col')
    def __init__(self, context):
        if context:
            self.lineno, self.col = context[1]
    def __iter__(self):
        return iter(self.children)
    def __getitem__(self, index):
        return self.children[index]
    def __pretty__(self, p, cycle):
        if cycle:
            return '{}(...)'.format(self.__class__.__name__)
        else:
            with p.group(4, self.__class__.__name__+'(', ')'):
                for (idx, ch) in enumerate(self.children):
                    if idx:
                        p.text(',')
                        p.breakable()
                    p.pretty(ch)

class GenericNode(Node):
    """Some dummy to have untyped parse tree for printing.
    Useful for debugging only
    """
    __slots__ = ('children', '__dict__')
    def __init__(self, children, context):
        self.children = children
        super().__init__(context)

class Leaf(Node):
    __slots__ = ('type', 'value')
    def __init__(self, value, context):
        self.value = value
        super().__init__(context)
    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.value)
    def __pretty__(self, p, c):
        return p.text(repr(self))

class Name(Leaf):
    __slots__ = ()

class String(Leaf):
    __slots__ = ()
    def __init__(self, value, context):
        if value.startswith("'''"):
            assert value.endswith("'''")
            value = value[3:-3]
        elif value.startswith('"""'):
            assert value.endswith('"""')
            value = value[3:-3]
        elif value.startswith('"'):
            assert value.endNameswith('"')
            value = value[1:-1]
        elif value.startswith("'"):
            assert value.endswith("'")
            value = value[1:-1]
        else:
            raise NotImplementedError(value)
        value = '\\'.join(map(self._rep,value.split(r'\\')))
        super().__init__(value, context)
    def _rep(self, val):
        return val.replace(r'\"', '"').replace(r"\'", "'")\
            .replace(r'\r', '\r').replace(r'\n', '\n')
    def __repr__(self):
        return '<String {!r}>'.format(self.value)

class Number(Leaf):
    __slots__ = ()
    def __init__(self, value, context):
        if '.' in value:
            value = float(value)
        else:
            value = int(value)
        super().__init__(value, context)
    def _rep(self, val):
        return val.replace(r'\"', '"').replace(r"\'", "'")\
            .replace(r'\r', '\r').replace(r'\n', '\n')
    def __repr__(self):
        return '<String {!r}>'.format(self.value)

class DottedName(Leaf):
    __slots__ = ('parts',)
    def __init__(self, children, context):
        self.parts = list(map(attrgetter('value'), children))
        super().__init__('.'.join(self.parts), context)
    def __repr__(self):
        return '<Dotname {}>'.format('.'.join(self.parts))

class Op(Leaf):
    __slots__ = ()

class ImportStmt(Node):
    __slots__ = ('module', 'names')
    def __init__(self, children, context):
        _from, self.module, _import, self.names = children
        assert _from.value == 'from', _from
        assert _import.value == 'import', _import
        super().__init__(context)
    @property
    def children(self):
        yield self.module
        yield self.names

class Assign(Node):
    __slots__ = ('target', 'expr')
    def __init__(self, children, context):
        self.target, _eq, self.expr = children
        assert _eq.value == '=', _eq
        super().__init__(context)
    @property
    def children(self):
        yield self.target
        yield self.expr

class Decorator(Node):
    __slots__ = ('name', 'arguments')
    def __init__(self, children, context):
        self.name, self.arguments = children
        super().__init__(context)
    @property
    def children(self):
        yield self.name
        yield self.arguments

class Class(Node):
    __slots__ = ('decorators', 'name', 'bases', 'body')
    def __init__(self, children, context):
        self.decorators = None
        _class, self.name, self.bases, self.body = children
        assert _class.value == 'class'
        super().__init__(context)
    @property
    def children(self):
        yield self.decorators
        yield self.name
        yield self.bases
        yield self.body

class Func(Node):
    __slots__ = ('decorators', 'name', 'arguments', 'body')
    def __init__(self, children, context):
        self.decorators = None
        _def, self.name, self.arguments, self.body = children
        assert _def.value == 'def'
        super().__init__(context)
    @property
    def children(self):
        yield self.decorators
        yield self.name
        yield self.arguments
        yield self.body

class Tuple(GenericNode):
    __slots__ = ()

class FileInput(GenericNode):
    __slots__ = ('used_names',)

def Nop(val, ctx):
    return

def TName(child, ctx):
    if len(child) > 1:
        return Assoc(child, ctx)
    else:
        return child[0]

def List(child, ctx):
    return child

def _Tuple(child, ctx):
    if len(child) > 1:
        return Tuple(child, ctx)
    else:
        return child[0]

def Skip(child, ctx):
    assert len(child) == 1, child
    return child[0]

def Atom(child, ctx):
    if len(child) == 1:
        return child[0]
    assert all(isinstance(v, String) for v in child)
    child[0].value = ''.join(map(attrgetter('value'), child))
    return child[0]

def Power(child, ctx):
    if len(child) < 2:
        return child[0]
    res = child[0]
    for n in child[1:]:
        res = GenericNode([res, n], ('', (res.lineno, res.col)))
    return res

def _Assign(child, ctx):
    if len(child) < 2:
        return child[0]
    return Assign(child, ctx)

def Factor(child, ctx):
    if len(child) < 2:
        return child[0]
    raise NotImplementedError(child)

def NotTest(child, ctx):
    if len(child) < 2:
        return child[0]
    raise NotImplementedError(child)

def Test(child, ctx):
    if len(child) < 2:
        return child[0]
    raise NotImplementedError(child)

def GenExp(child, ctx):
    if len(child) < 2:
        return child[0]
    raise NotImplementedError(child)

class Binary(Node):
    __slots__ = ('left', 'right')
    def __init__(self, left, right, context):
        self.left = left
        self.right = right
        super().__init__(context)
    @property
    def children(self):
        yield self.left
        yield self.right
class Add(Binary):
    __slots__ = ()
class Subtract(Binary):
    __slots__ = ()
class Multiply(Binary):
    __slots__ = ()
class Divide(Binary):
    __slots__ = ()
class Modulo(Binary):
    __slots__ = ()

operators = {
    '+': Add,
    '-': Subtract,
    '*': Multiply,
    '/': Divide,
    '%': Modulo,
    }
def Term(child, ctx):
    """Any binary operators are here. Precedence is handled by parser"""
    if len(child) < 2:
        return child[0]
    it = iter(child)
    pre = next(it)
    for op in it:
        nex = next(it)
        pre = operators[op.value](pre, nex, ('', (op.lineno, op.col)))
    return pre

def Decorated(child, ctx):
    assert not child[1].decorators
    child[1].decorators = child[0]
    return child[1]

class Trail(Node):
    __slots__ = ('expr',)
class Call(Trail):
    __slots__ = ('arguments',)
    def __init__(self, child, context):
        self.expr = None
        if child:
            assert len(child) == 1
            self.arguments = child[0]
        else:
            self.arguments = []
        super().__init__(context)
    @property
    def children(self):
        yield self.expr
        yield self.arguments
class CallAttr(Trail):
    __slots__ = ('attribute', 'arguments',)
    def __init__(self, children, context):
        self.expr, self.attribute, self.arguments = children
        super().__init__(context)
    @property
    def children(self):
        yield self.expr
        yield self.attribute
        yield self.arguments
class Subscr(Trail):
    __slots__ = ('index',)
    def __init__(self, child, context):
        self.expr = None
        assert len(child) == 1
        self.index = child[0]
        super().__init__(context)
    @property
    def children(self):
        yield self.expr
        yield self.index
class GetAttr(Trail):
    __slots__ = ('name',)
    def __init__(self, child, context):
        self.expr = None
        assert len(child) == 1
        self.name = child[0]
        super().__init__(context)
    @property
    def children(self):
        yield self.expr
        yield self.name

class Super(Trail):
    __slots__ = ('method', 'arguments')
    def __init__(self, child, context):
        self.method = child[0]
        self.arguments = child[1]
        super().__init__(context)
    @property
    def children(self):
        yield self.method
        yield self.arguments

def Trailered(child, ctx):
    if len(child) < 2:
        return child[0]
    p = child[0]
    for n in child[1:]:
        assert not n.expr
        if isinstance(n, Call) and isinstance(p, GetAttr):
            if isinstance(p.expr, Call) and isinstance(p.expr.expr, Name)\
                and p.expr.expr.value == 'super':
                n = Super([p.name, n.arguments],
                    ('', (n.lineno, n.col)))
            else:
                n = CallAttr([p.expr, p.name, n.arguments],
                    ('', (n.lineno, n.col)))
        else:
            n.expr = p
        p = n
    return n

tokens = {
    token.INDENT: Nop,
    token.NEWLINE: Nop,
    token.LPAR: Nop,
    token.RPAR: Nop,
    token.AT: Nop,
    token.NAME: Name,
    token.DOT: Nop,
    token.COLON: Nop,
    token.STRING: String,
    token.DEDENT: Nop,
    token.ENDMARKER: Nop,
    token.EQUAL: Op,
    token.PLUS: Op,
    token.MINUS: Op,
    token.STAR: Op,
    token.NUMBER: Number,
    token.SLASH: Op,
    token.COMMA: Nop,
    }

symbols = {
    symbol.dotted_name: DottedName,
    symbol.import_as_name: TName,
    symbol.import_as_names: List,
    symbol.import_stmt: ImportStmt,
    symbol.small_stmt: Skip,
    symbol.simple_stmt: Skip,
    symbol.stmt: Skip,
    symbol.atom: Atom,
    symbol.power: Power,
    symbol.factor: Factor,
    symbol.term: Term,
    symbol.arith_expr: Term,
    symbol.shift_expr: Term,
    symbol.and_expr: Term,
    symbol.xor_expr: Term,
    symbol.expr: Term,
    symbol.comparison: Term,
    symbol.not_test: NotTest,
    symbol.and_test: Term,
    symbol.or_test: Term,
    symbol.test: Test,
    symbol.argument: Skip,
    symbol.arglist: List,
    symbol.typedargslist: List,
    symbol.parameters: Skip,
    symbol.compound_stmt: Skip,
    symbol.suite: List,
    symbol.decorator: Decorator,
    symbol.decorators: List,
    symbol.tname: TName,
    symbol.tfpdef: Skip,
    symbol.trailer: Term,
    symbol.trailattr: GetAttr,
    symbol.trailsubscr: Subscr,
    symbol.trailcall: Call,
    symbol.trailered: Trailered,
    symbol.testlist: _Tuple,
    symbol.expr_stmt: _Assign,
    symbol.funcdef: Func,
    symbol.classdef: Class,
    symbol.decorated: Decorated,
    symbol.testlist_gexp: GenExp,
    symbol.file_input: FileInput,
    }

def convert(gr, raw_node):
    """
    Convert raw node information to a Node or Leaf instance.

    This is passed to the parser driver which calls it whenever a reduction of a
    grammar rule produces a new complete node, so that the tree is build
    strictly bottom-up.
    """
    type, value, context, children = raw_node
    if not children:
        t = tokens.get(type, None)
        if t is not None:
            return t(value, context)
    t = symbols.get(type, None)
    if t is not None:
        return t(children, context)
    try:
        raise NotImplementedError(grammar.number2symbol[type])
    except KeyError:
        raise NotImplementedError(token.tok_name[type])

def parser():
    driv = driver.Driver(grammar, convert=convert)
    return driv

if __name__ == '__main__':
    import sys
    driv = parser()
    with open(sys.argv[1], 'r') as f:
        ast = driv.parse_string(f.read())
        pretty.pprint(ast)
