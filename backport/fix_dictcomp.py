from lib2to3 import fixer_base, pytree
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Name, Call, LParen, RParen, ArgList, Dot

"""
Fixes:
    {a:b for a,b in abc}
into:
    dict((a,b) for a, b in abc)
"""

class FixDictcomp(fixer_base.BaseFix):
    PATTERN = """
        atom< '{' dictsetmaker< key=any ':' value=any
            cfor=comp_for<any*> > '}' >
    """
    def transform(self, node, results):
        syms = self.syms
        results['key'].remove()
        results['cfor'].remove()
        results['value'].remove()
        res = pytree.Node(syms.power,
            [Name('dict', prefix=node.prefix),
             pytree.Node(syms.trailer,
                [pytree.Leaf(token.LPAR, '('),
                 pytree.Node(syms.argument,
                    [pytree.Node(syms.atom,
                        [pytree.Leaf(token.LPAR, '('),
                         pytree.Node(syms.testlist_gexp,
                            [results['key'],
                             pytree.Leaf(token.COMMA, ','),
                             results['value']]),
                         pytree.Leaf(token.RPAR, ')')]),
                     results['cfor']]),
                 pytree.Leaf(token.RPAR, ')')])])
        return res
