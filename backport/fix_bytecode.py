
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import LParen, RParen, Comma

"""
Fixes:
    ('name', str, 'string', ...)
    ('name', unicode, 'string', ...)
into:
    ('name', basestring, 'string', ...)
"""

class FixBytecode(fixer_base.BaseFix):
    PATTERN = r"""
        atom< '(' testlist_gexp< any ',' type=('str'|'unicode')
            ',' str=any ',' any* > ')' >
    """

    def transform(self, node, results):
        if getattr(results['str'], 'value', None) == "u'string'":
            results['type'][0].value = 'basestring'
        return node
