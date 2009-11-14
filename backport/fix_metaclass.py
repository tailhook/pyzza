
from lib2to3 import fixer_base, pytree
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Assign, Name, Newline

"""
Fixes:
    class a(metaclass=b): ...
into:
    class a:
        __metaclass__ = b
"""

class FixMetaclass(fixer_base.BaseFix):
    PATTERN = """
        classdef< 'class' any '('
            arglist< any* arg=argument< 'metaclass' '=' meta=any > > ')' ':'
            suite = any >
        |
        classdef< 'class' any '('
            arg=argument< 'metaclass' '=' meta=any > ')' ':'
            suite = any >
    """
    def transform(self, node, results):
        syms = self.syms
        results['arg'].remove()
        results['meta'].remove()
        for i in results['suite'].children:
            if i.prefix and i.prefix != '\n':
                pref = i.prefix
                break
        else:
            pref = node.prefix + '    '
        results['suite'].insert_child(1,
            pytree.Node(syms.simple_stmt,
                [Assign(Name('__metaclass__'), results['meta']),
                 Newline()], prefix=pref))
        return node


