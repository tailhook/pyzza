from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Call, Name, Comma

"""
Fixes:
    b''.join(...)
into:
    b''.join(map(bytes, ...))
"""

class FixJoinbytes(fixer_base.BaseFix):
    PATTERN = """
        power< bytes=STRING trailer< '.' 'join' > trailer< '(' arg=any ')' > >
    """

    def transform(self, node, results):
        if results['bytes'].value.startswith('b'):
            results['arg'].replace(Call(Name('map'), [
                Name('bytes'),
                Comma(),
                results['arg'].clone(),
                ]))
        return node


