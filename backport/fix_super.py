
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import LParen, RParen, Comma

"""
Fixes:
    super()
into:
    super(Classname, self)
"""

class FixSuper(fixer_base.BaseFix):
    PATTERN = """
        power< 'super' parens=trailer< '(' ')' > any* >
    """

    CLASSPAT = """
        classdef< 'class' clsname=any any*>
    """
    classpat = patcomp.compile_pattern(CLASSPAT)
    FUNCPAT = """
        funcdef< 'def' any parameters< '('
            typedargslist< firstarg=any any* > ')' > ':' any* >
        |
        funcdef< 'def' any parameters< '('
            firstarg=any ')' > ':' any* >
    """
    funcpat = patcomp.compile_pattern(FUNCPAT)

    def transform(self, node, results):
        syms = self.syms
        fun = node
        funres = {}
        while fun and not self.funcpat.match(fun, funres):
            fun = fun.parent
        cls = fun
        clsres = {}
        while cls and not self.classpat.match(cls, clsres):
            cls = cls.parent
        results['parens'].insert_child(1,
                pytree.Node(syms.arglist, [
                    clsres['clsname'].clone(),
                    Comma(),
                    funres['firstarg'].clone()]))
        return node


