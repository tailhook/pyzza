from lib2to3 import fixer_base, pytree
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Name, Call, LParen, RParen, ArgList, Dot

"""
Fixes:
    with a as b, c as d:
        pass
into:
    with nested(a, b) as (c, d):
        pass
"""

class FixWithnest(fixer_base.BaseFix):
    PATTERN = """
        with_stmt< 'with'
            withitems=any* ':'
            any* >
    """
    def transform(self, node, results):
        syms = self.syms
        if len(results['withitems']) == 1:
            return node
        for i in results['withitems'][1:]:
            i.remove()
        contexts = []
        vars = []
        for i in results['withitems']:
            if i.type == syms.with_item:
                a = i.children[0]
                a.remove()
                b = i.children[1]
                b.remove()
                contexts.append(a)
                vars.append(b)
            elif str(i) == ',':
                i.remove()
                contexts.append(i.clone())
                vars.append(i)
            else:
                i.remove()
                contexs.append(i)
                vars.append(Name('_skip'))
        results['withitems'][0].replace(
            pytree.Node(syms.with_item,
                [pytree.Node(syms.power,
                    [Name('nested', prefix=' '),
                     pytree.Node(syms.trailer,
                        [pytree.Leaf(token.LPAR, '('),
                         pytree.Node(syms.arglist,
                            contexts),
                         pytree.Leaf(token.RPAR, ')')])]),
                 Name('as', prefix=' '),
                 pytree.Node(syms.atom,
                    [pytree.Leaf(token.LPAR, '('),
                     pytree.Node(syms.testlist_gexp,
                        vars),
                     pytree.Leaf(token.RPAR, ')')],
                    prefix=' ')]))
        return node
