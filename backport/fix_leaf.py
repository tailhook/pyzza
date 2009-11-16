


from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Call, Name

"""
Fixes:
    class Leaf:
        ...
        def ...
            self.value = value
into:
    class Leaf:
        ...
        def ...
            sef.value = unicode(value)
"""

class FixLeaf(fixer_base.BaseFix):
    PATTERN = """
        classdef< 'class' 'Leaf' any* suite< any*
            funcdef< any* suite< any*
            simple_stmt< expr_stmt< power< 'self' trailer< '.' 'value' > >
                '=' val='value' >
            any* > any* > > any* > >
    """

    def transform(self, node, results):
        results['val'].replace(Call(Name('unicode'), [results['val'].clone()]))
        return node



