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
    def __len__(self):
        return len(self.children)
    def __pretty__(self, p, cycle):
        if cycle:
            return '{}(...)'.format(self.__class__.__name__)
        else:
            with p.group(4, self.__class__.__name__+'(', ')'):
                try:
                    ch = iter(self.children)
                except AttributeError:
                    p.text(repr(self))
                    return
                for (idx, ch) in enumerate(ch):
                    if idx:
                        p.text(',')
                        p.breakable()
                    p.pretty(ch)

class GenericNode(Node):
    """Some dummy to have untyped parse tree for printing.
    Useful for debugging only
    """
    __slots__ = ('children',)
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
            assert value.endswith('"')
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
            value = int(value, 0)
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

class Return(Node):
    __slots__ = ('expr',)
    def __init__(self, children, context):
        _return, self.expr = children
        assert _return.value == 'return', _return
        super().__init__(context)
    @property
    def children(self):
        yield self.expr

class Del(Node):
    __slots__ = ('expr',)
    def __init__(self, children, context):
        _del, self.expr = children
        assert _del.value == 'del', _del
        super().__init__(context)
    @property
    def children(self):
        yield self.expr

class Raise(Node):
    __slots__ = ('expr',)
    def __init__(self, children, context):
        _raise, self.expr = children
        assert _raise.value == 'raise', _raise
        super().__init__(context)
    @property
    def children(self):
        yield self.expr

class Break(Node):
    __slots__ = ()
    def __init__(self, children, context):
        _break, = children
        assert _break.value == 'break', _break
        super().__init__(context)

class Continue(Node):
    __slots__ = ()
    def __init__(self, children, context):
        _continue, = children
        assert _continue.value == 'continue', _continue
        super().__init__(context)

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

class If(Node):
    __slots__ = ('ifs', 'else_')
    def __init__(self, children, context):
        self.ifs = []
        self.else_ = None
        chit = iter(children)
        for k in chit:
            if k.value in ('if', 'elif'):
                self.ifs.append((next(chit), next(chit)))
            else:
                assert k.value == 'else', k
                self.else_ = next(chit)
        super().__init__(context)
    @property
    def children(self):
        for (k, v) in self.ifs:
            yield k
            yield v
        if self.else_:
            yield self.else_

class For(Node):
    __slots__ = ('var', 'expr', 'body', 'else_')
    def __init__(self, children, context):
        _for, self.var, _in, self.expr, self.body = children[:5]
        self.else_ = None
        assert _for.value == 'for', _for
        assert _in.value == 'in', _in
        if len(children) > 5:
            _else, self.else_ = children[5:]
            assert _else.value == 'else', _else
        super().__init__(context)
    @property
    def children(self):
        yield self.var
        yield self.expr
        yield self.body
        if self.else_:
            yield self.else_

class While(Node):
    __slots__ = ('condition', 'body', 'else_')
    def __init__(self, children, context):
        _while, self.condition, self.body = children[:3]
        self.else_ = None
        assert _while.value == 'while', _while
        if len(children) > 3:
            _else, self.else_ = children[3:]
            assert _else.value == 'else', _else
        super().__init__(context)
    @property
    def children(self):
        yield self.condition
        yield self.body
        if self.else_:
            yield self.else_

class Try(Node):
    __slots__ = ('body', 'excepts', 'except_', 'else_', 'finally_')
    def __init__(self, children, context):
        ch = iter(children)
        _try = next(ch)
        assert _try.value == 'try', _try
        self.excepts = []
        self.except_ = None
        self.finally_ = None
        self.else_ = None
        self.body = next(ch)
        for tok in ch:
            if isinstance(tok, Tuple): #except_clause
                assert self.except_ is None
                assert self.else_ is None
                assert self.finally_ is None
                tok = tok.children
                if len(tok) < 2:
                    _except, = tok
                    assert _except.value == 'except', _except
                    self.except_ = next(ch)
                elif len(tok) < 3:
                    _except, typ = tok
                    suite = next(ch)
                    assert _except.value == 'except', _except
                    self.excepts.append((typ, None, suite))
                elif len(tok) < 5:
                    _except, typ, _as, name = tok
                    suite = next(ch)
                    assert _except.value == 'except', _except
                    assert _as.value == 'as', _as
                    self.excepts.append((typ, name, suite))
                else:
                    raise NotImplementedError(tok)
            elif tok.value == 'else':
                assert self.finally_ is None
                assert self.else_ is None
                assert self.excepts or self.except_
                self.else_ = next(ch)
            elif tok.value == 'finally':
                assert self.finally_ is None
                self.finally_ = next(ch)
            else:
                raise NotImplementedError(tok)
        super().__init__(context)
    @property
    def children(self):
        yield self.body
        for i in self.excepts:
            for k in i:
                if k is not None:
                    yield k
        if self.except_:
            yield self.except_
        if self.else_:
            yield self.else_
        if self.finally_:
            yield self.finally_

class Assign(Node):
    __slots__ = ('target', 'operator', 'expr')
    def __init__(self, children, context):
        self.target, self.operator, self.expr = children
        assert self.operator.value[-1] == '=', self.operator
        super().__init__(context)
    @property
    def children(self):
        yield self.target
        yield self.expr

class Decorator(Node):
    __slots__ = ('name', 'arguments')
    def __init__(self, children, context):
        if len(children) > 1:
            self.name, self.arguments = children
        else:
            self.name = children[0]
            self.arguments = []
        super().__init__(context)
    @property
    def children(self):
        yield self.name
        yield self.arguments

class Class(Node):
    __slots__ = ('decorators', 'name', 'bases', 'body', '__dict__')
    def __init__(self, children, context):
        self.decorators = None
        if len(children) < 4:
            _class, self.name, self.body = children
            self.bases = []
        else:
            _class, self.name, self.bases, self.body = children
        assert _class.value == 'class'
        super().__init__(context)
    @property
    def children(self):
        if self.decorators:
            yield self.decorators
        yield self.name
        yield self.bases
        yield self.body

class Func(Node):
    __slots__ = ('decorators', 'name', 'arguments', 'body', '__dict__')
    def __init__(self, children, context):
        self.decorators = None
        _def, self.name, self.arguments, self.body = children
        assert _def.value == 'def'
        super().__init__(context)
    @property
    def children(self):
        if self.decorators:
            yield self.decorators
        yield self.name
        yield self.arguments
        yield self.body

class Tuple(GenericNode):
    __slots__ = ()

class ListMaker(GenericNode):
    __slots__ = ()

def _ListMaker(children, context):
    if children:
        assert len(children) == 1, children
        assert isinstance(children[0], ListMaker)
        return children[0]
    else:
        return ListMaker([], context)

class DictMaker(GenericNode):
    __slots__ = ()

def _DictMaker(children, context):
    if children:
        assert len(children) == 1, children
        assert isinstance(children[0], DictMaker)
        return children[0]
    else:
        return DictMaker([], context)

class Parameters(GenericNode):
    __slots__ = ()

class Argument(Node):
    __slots__ = ('name', 'type', 'default')
    def __init__(self, children, context):
        self.name = children[0]
        if len(children) > 1:
            if children[1].value == '=':
                assert len(children) == 3
                self.default = children[2]
            elif children[1].value == ':':
                self.type = children[2]
                if len(children) > 3:
                    assert len(children) == 5
                    assert children[3].value == '='
                    self.default = children[4]
        super().__init__(context)

class Vararg(Argument):
    __slots__ = ()
    def __init__(self, children, context):
        assert children[0].value == '*'
        super().__init__(children[1:], context)

def _Parameters(children, context):
    if children:
        assert len(children) == 1, children
        assert isinstance(children[0], Parameters)
        return children[0]
    else:
        return Parameters([], context)

class FileInput(GenericNode):
    pass

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
    assert len(child) == 1, (child, ctx)
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

class Negate(Node):
    __slots__ = ('expr',)
    def __init__(self, children, context):
        _neg, self.expr = children
        assert _neg.value == '-', _neg
        super().__init__(context)

def Factor(child, ctx):
    if len(child) < 2:
        return child[0]
    if child[0].value == '-':
        return Negate(child, ctx)
    raise NotImplementedError(child)

class NotTest(Node):
    __slots__ = ('expr',)
    def __init__(self, children, context):
        _not, self.expr = children
        assert _not.value == 'not', _not
        super().__init__(context)
    @property
    def children(self):
        return self.expr

def _NotTest(child, ctx):
    if len(child) < 2:
        return child[0]
    return NotTest(child, ctx)

def Test(child, ctx):
    if len(child) < 2:
        return child[0]
    raise NotImplementedError(child)

def GenExp(child, ctx):
    if len(child) < 2:
        return child[0]
    if getattr(child[1], 'value', None) != 'for':
        return Tuple(child, ctx)
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
class Greater(Binary):
    __slots__ = ()
class GreaterEq(Binary):
    __slots__ = ()
class Less(Binary):
    __slots__ = ()
class LessEq(Binary):
    __slots__ = ()
class And(Binary):
    __slots__ = ()
class Or(Binary):
    __slots__ = ()
class Equal(Binary):
    __slots__ = ()
class NotEqual(Binary):
    __slots__ = ()

operators = {
    '+': Add,
    '-': Subtract,
    '*': Multiply,
    '/': Divide,
    '%': Modulo,
    '>': Greater,
    '>=': GreaterEq,
    '<': Less,
    '<=': LessEq,
    '!=': NotEqual,
    '==': Equal,
    'or': Or,
    'and': And,
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
    token.LSQB: Nop,
    token.RSQB: Nop,
    token.LBRACE: Nop,
    token.RBRACE: Nop,
    token.PLUS: Op,
    token.MINUS: Op,
    token.STAR: Op,
    token.SLASH: Op,
    token.PERCENT: Op,
    token.NUMBER: Number,
    token.COMMA: Nop,
    token.GREATER: Op,
    token.GREATEREQUAL: Op,
    token.LESS: Op,
    token.LESSEQUAL: Op,
    token.EQUAL: Op,
    token.PLUSEQUAL: Op,
    token.EQEQUAL: Op,
    token.NOTEQUAL: Op,
    token.STAREQUAL: Op,
    token.MINEQUAL: Op,
    token.SLASHEQUAL: Op,
    token.PERCENTEQUAL: Op,
    }

symbols = {
    symbol.dotted_name: DottedName,
    symbol.import_as_name: TName,
    symbol.import_as_names: List,
    symbol.import_stmt: ImportStmt,
    symbol.small_stmt: Skip,
    symbol.simple_stmt: Skip,
    symbol.stmt: Skip,
    symbol.augassign: Skip,
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
    symbol.not_test: _NotTest,
    symbol.and_test: Term,
    symbol.or_test: Term,
    symbol.test: Test,
    symbol.argument: Skip,
    symbol.pass_stmt: Skip,
    symbol.arglist: List,
    symbol.typedargslist: Parameters,
    symbol.parameters: _Parameters,
    symbol.compound_stmt: Skip,
    symbol.suite: List,
    symbol.decorator: Decorator,
    symbol.decorators: List,
    symbol.tname: TName,
    symbol.tfpdef: Skip,
    symbol.trailer: Term,
    symbol.comp_op: Term,
    symbol.trailattr: GetAttr,
    symbol.trailsubscr: Subscr,
    symbol.subscript: Skip,
    symbol.subscriptlist: Skip,
    symbol.trailcall: Call,
    symbol.trailered: Trailered,
    symbol.testlist: _Tuple,
    symbol.exprlist: Tuple,
    symbol.expr_stmt: _Assign,
    symbol.funcdef: Func,
    symbol.classdef: Class,
    symbol.flow_stmt: Skip,
    symbol.if_stmt: If,
    symbol.for_stmt: For,
    symbol.while_stmt: While,
    symbol.try_stmt: Try,
    symbol.break_stmt: Break,
    symbol.continue_stmt: Continue,
    symbol.except_clause: Tuple,
    symbol.decorated: Decorated,
    symbol.return_stmt: Return,
    symbol.del_stmt: Del,
    symbol.raise_stmt: Raise,
    symbol.listmaker_in: ListMaker,
    symbol.listmaker: _ListMaker,
    symbol.dictmaker_in: DictMaker,
    symbol.dictmaker: _DictMaker,
    symbol.testlist_gexp: GenExp,
    symbol.typedarg: Argument,
    symbol.typedvararg: Vararg,
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
