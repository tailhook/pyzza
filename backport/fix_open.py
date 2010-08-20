
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import LParen, RParen, Comma

"""
Fixes:
    open(a, b, encoding=)
into:
    open(a, b)
"""

class FixOpen(fixer_base.BaseFix):
    PATTERN = """
        power< 'open' trailer< '(' arglist< any ',' any
            comma=',' enc=argument< 'encoding' '=' any > > ')' > >
    """

    def transform(self, node, results):
        results['comma'].remove()
        results['enc'].remove()
        return node
