
from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import LParen, RParen, Comma

"""
Fixes:
    open(a, b, encoding=)
into:
    open(a, b)
"""

class FixCollections(fixer_base.BaseFix):
    PATTERN = """
        import_from< 'from' modulename='collections' 'import'
            import_as_names< 'defaultdict' ',' import_as_name< 'OrderedDict' 'as' 'ordereddict' > > >
    """

    def transform(self, node, results):
        results['modulename'].value = '.collections'
        return node
