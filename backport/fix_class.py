
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import ArgList, Name

"""
Fixes:
    class Name: ...
into:
    class Name(object): ...
"""

class FixClass(fixer_base.BaseFix):
    PATTERN = """
        classdef< 'class' any ':' any* >
    """

    def transform(self, node, results):
        node.insert_child(2, ArgList([Name('object')]))
        return node


