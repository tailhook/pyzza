from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Call, Comma, Name

"""
Fixes:
    for file in args: ...
into:
    for file in map(unicode, args): ...
"""

class FixFileinargs(fixer_base.BaseFix):
    PATTERN = """
        for_stmt< 'for' 'file' 'in' arg='args' ':' any* >
    """

    def transform(self, node, results):
        results['arg'].replace(Call(Name('map'), [
            Name('unicode'),
            Comma(),
            results['arg'].clone(),
            ], prefix=results['arg'].prefix))
        return node



