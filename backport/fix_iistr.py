
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import LParen, RParen, Comma

"""
Fixes:
    isinstance(..., str)
into:
    isinstance(..., unicode)
"""

class FixIistr(fixer_base.BaseFix):
    PATTERN = """
        power< 'isinstance' trailer< '(' arglist< any ',' type='str' > ')' > >
    """

    def transform(self, node, results):
        results['type'].value = 'unicode'
        return node


