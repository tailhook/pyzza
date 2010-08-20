
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import LParen, RParen, Comma

"""
Fixes:
    add_option(u"-a"
into:
    add_option("-a"
"""

class FixOptparser(fixer_base.BaseFix):
    PATTERN = """
        power< any* trailer< '.' 'add_option' >
            trailer< '(' args=arglist< any* > ')' > any* >
    """

    def transform(self, node, results):
        for ch in results['args'].children:
            if hasattr(ch, 'value') and ch.value.startswith(("u'", 'u"')):
                ch.value = ch.value[1:]
        return node
