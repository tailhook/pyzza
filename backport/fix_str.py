
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Leaf

"""
Fixes:
    str
into:
    unicode
"""

class FixStr(fixer_base.BaseFix):
    PATTERN = """
        'str'
    """

    def transform(self, node, results):
        node.value = 'unicode'
        return node


