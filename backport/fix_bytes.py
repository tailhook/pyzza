from lib2to3 import fixer_base, pytree, patcomp
from lib2to3.pgen2 import token
from lib2to3.fixer_util import Call, Name, Comma

"""
Fixes:
    bytes([...])
into:
    bytearray([...])
"""

class FixBytes(fixer_base.BaseFix):
    PATTERN = """
        power< name='bytes' trailer< '(' atom< '[' any ']' > ')' > >
    """

    def transform(self, node, results):
        results['name'].value = 'bytearray'
        return node


