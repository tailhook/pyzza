from lepl import Token, Or, Delayed, Node, LineAwareConfiguration, Line, AnyBut
from lepl import Repeat, Extend
from lepl import UnsignedFloat
from lepl import ContinuedBLineFactory
from lepl import Block, Empty, Eof
from lepl import RecordDeepest, Trace

from logging import basicConfig, getLogger, INFO, DEBUG
basicConfig(level=INFO)

class Add(Node): pass
class Sub(Node): pass
class Div(Node): pass
class Mul(Node): pass
class Per(Node): pass
class Pow(Node): pass

class String(Node): pass
class GetItem(Node): pass
class GetAttr(Node): pass
class Subscript(Node): pass
class Call(Node): pass

def subscript(lst):
    if len(lst) == 1:
        return lst[0]
    return Subscript(*lst)

class Lt(Node): pass
class Le(Node): pass
class Gt(Node): pass
class Ge(Node): pass
class Eq(Node): pass
class Ne(Node): pass

class If(Node): pass
class For(Node): pass

class Return(Node): pass
class Print(Node): pass
class Assert(Node): pass
class Assign(Node): pass
class FromImport(Node): pass

class DotName(Node): pass

class BlockStmt(Node): pass
class Class(Node): pass
class Def(Node): pass

def parsers():
    symbol = Token(r'[\+\-\*\(\):/%=<>\.,\[\]]')
    ident = Token('[a-zA-Z_][a-zA-Z_0-9]*')

    def mkstring(quote):
        return Token("{0}[^{0}]*{0}".format(quote))

    float_ = Token(UnsignedFloat()) >> float
    negfloat = ~symbol('-') & Token(UnsignedFloat()) >> (lambda x: -float(x))
    number = float_ | negfloat
    varname = ident

    group1, group2, group3, group4 = Delayed(), Delayed(), Delayed(), Delayed()

    parens = ~symbol('(') & Extend(group3) & ~symbol(')')
    string = (mkstring('"') | mkstring("'")) > String
    group0, group05, expr = Delayed(), Delayed(), Delayed()
    getitem = ~symbol('[') & Extend(expr) & ~symbol(']') > GetItem
    getattr = ~symbol('.') & varname > GetAttr
    lvalue = group0 & (getitem | getattr)[:] > subscript
    args = expr & (~symbol(',') & expr)[:] > list
    call = ~symbol('(') & Extend(args[:1]) & ~symbol(')') > Call
    group0 += parens | number | string | varname
    group05 += group0 & (getitem | getattr | call)[:] > subscript

    pow = group05 & ~Token(r'\*\*') & group1 > Pow
    group1 += pow | group05
    mul = group1 & ~symbol('*') & group2 > Mul
    div = group1 & ~symbol('/') & group2 > Div
    per = group1 & ~symbol('%') & group2 > Per
    group2 += mul | div | per | group1
    add = group2 & ~symbol('+') & group3 > Add
    sub = group2 & ~symbol('-') & group3 > Sub
    group3 += add | sub | group2
    lt = group3 & ~symbol('<') & group4 > Lt
    le = group3 & ~Token('<=') & group4 > Le
    gt = group3 & ~symbol('>') & group4 > Gt
    ge = group3 & ~Token('>=') & group4 > Ge
    eq = group3 & ~Token('==') & group4 > Eq
    ne = group3 & ~Token('!=') & group4 > Ne
    group4 += lt | le | gt | ge | eq | ne | group3
    and_, or_, xor_ = Delayed(), Delayed(), Delayed()
    and_ = group4 & ~ident('and') & and_ | group4
    or_ = group4 & ~ident('or') & or_ | group4
    expr += or_

    dotname = varname & (~symbol('.') & varname)[:] > DotName

    colon = ~symbol(':')
    if_stmt = ~ident('if') & expr & colon > If
    for_stmt = ~ident('for') & lvalue & ~ident('in') & expr & colon > For
    bases = Delayed()
    bases += varname & symbol(',') & bases | varname  > list
    _bases = ~symbol('(') & bases & ~symbol(')')
    class_stmt = ~ident('class') & varname & _bases[:1] & colon > Class
    argdef = varname & (~symbol(',') & varname)[:] > list
    _argdef = ~symbol('(') & args[:] & ~symbol(')')
    def_stmt = ~ident('def') & varname & _argdef & colon > Def
    open_stmt = if_stmt | for_stmt | class_stmt | def_stmt

    pass_stmt = ~ident('pass')
    print_stmt = ~ident('print') & expr > Print
    return_stmt = ~ident('return') & expr > Return
    assert_stmt = ~ident('assert') & expr > Assert
    assign_stmt = lvalue & ~symbol('=') & expr > Assign
    from_stmt = ~ident('from') & dotname & ~ident('import') & varname > FromImport

    BLine = ContinuedBLineFactory(r'\\')
    statement = Delayed()
    single = BLine(expr | from_stmt | class_stmt | pass_stmt
        | print_stmt | assert_stmt | return_stmt | Trace(assign_stmt))
    empty = BLine(Empty())
    block = BLine(open_stmt) & Block(statement[1:]) > BlockStmt
    statement += Or(block, single, empty)
    file_parser = (statement[:] & Eof()).file_parser(LineAwareConfiguration(
        block_policy=4, block_start=0,
        monitors=[RecordDeepest()],
        ))
    return file_parser

file_parser = parsers()

def parse_file(filename):
    with open(filename) as source:
        return file_parser(source)

def main():
    import optparse
    op = optparse.OptionParser()
    options, args = op.parse_args()
    if len(args) != 1:
        op.error("Exacly one argument expected")
    ast = parse_file(args[0])
    print(ast)
    for a in ast:
        print(a)

if __name__ == '__main__':
    main()
