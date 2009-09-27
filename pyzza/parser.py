from lepl import Token, Or, Delayed, Node, LineAwareConfiguration, Line, AnyBut
from lepl import Repeat, Extend, Any, throw
from lepl import UnsignedFloat
from lepl import ContinuedBLineFactory
from lepl import Block, Empty, Eof

from logging import basicConfig, INFO, DEBUG
basicConfig(level=INFO)


class Add(Node): pass
class Sub(Node): pass
class Div(Node): pass
class Mul(Node): pass
class Per(Node): pass
class Pow(Node): pass

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

symbol = Token(r'[\+\-\*\(\):/%=<>\.,]')
ident = Token('[a-zA-Z_][a-zA-Z_0-9]*')

def string(quote):
    return Token('{0}[^{0}]*{0}'.format(quote))

def bigstring(quote):
    #~ q = Token(quote)
    #~ content = Token(AnyBut(q))
    #~ content = Extend(Repeat(content, add_=True))
    #~ return ~q & content & ~q
    return string(quote)

float = Token(UnsignedFloat()) >> float
negfloat = ~symbol('-') & Token(UnsignedFloat()) >> (lambda x: -float(x))
number = float | negfloat
varname = ident

group1, group2, group3, group4 = Delayed(), Delayed(), Delayed(), Delayed()

parens = ~symbol('(') & group3 & ~symbol(')')
string = (string('"') | string("'")
    | bigstring(quote="'''") | bigstring(quote='"""')) > str
group0 = parens | number | string | varname

pow = group0 & ~Token(r'\*\*') & group1 > Pow
group1 += pow | group0
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
expr = group4

dotname = varname & (~symbol('.') & varname)[:] > DotName

colon = ~symbol(':')
if_stmt = ~ident('if') & expr & colon > If
for_stmt = ~ident('for') & expr & ~ident('in') & expr & colon > For
bases = Delayed()
bases += varname & symbol(',') & bases | varname  > list
_bases = ~symbol('(') & bases & ~symbol(')')
class_stmt = ~ident('class') & varname & _bases[:1] & colon > Class
args = varname & (~symbol(',') & varname)[:] > list
_args = ~symbol('(') & args[:1] & ~symbol(')')
def_stmt = ~ident('def') & varname & _args & colon > Def
open_stmt = if_stmt | for_stmt | class_stmt | def_stmt

pass_stmt = ~ident('pass')
print_stmt = ~ident('print') & expr > Print
return_stmt = ~ident('return') & expr > Return
assert_stmt = ~ident('assert') & expr > Assert
assign_stmt = varname & symbol('=') & expr > Assign
from_stmt = ~ident('from') & dotname & ~ident('import') & varname > FromImport

BLine = ContinuedBLineFactory(r'\\')
statement = Delayed()
single = BLine(expr | from_stmt | class_stmt | pass_stmt
    | print_stmt | assert_stmt | return_stmt | assign_stmt)
empty = BLine(Empty())
block = BLine(open_stmt) & Block(statement[1:]) > BlockStmt
statement += Or(block, single, empty)
parser = statement[:].file_parser(LineAwareConfiguration(
    block_policy=4, block_start=0,
    ))

def main():
    import optparse
    op = optparse.OptionParser()
    options, args = op.parse_args()
    if len(args) != 1:
        op.error("Exacly one argument expected")
    with open(args[0]) as source:
        ast = parser(source)
    print(ast)
    for a in ast:
        print(a)

if __name__ == '__main__':
    from .parser import main
    main()
