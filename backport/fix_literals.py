
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Leaf

"""
Fixes:
    a = 'abc'
into:
    a = u'abc'
"""

class FixLiterals(fixer_base.BaseFix):
    PATTERN = """
        STRING
    """


    def transform(self, node, results):
        if not node.value.startswith('b'):
            if not node.value[1] == '<': # dirty hack for struct functions
                node.value = 'u' + node.value
        return node


