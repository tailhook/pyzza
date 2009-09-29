from . import swf, tags
class Library:
    """
    This class holds a reference to all ABCFile structures of all files loaded
    as a library. So that subclasses can find out correct scope, method
    signatures and property namespaces can be checked, and some small methods
    can be inlined.
    """

    def __init__(self):
        self.code_headers = []

    def add_file(self, filename):
        with open(filename, 'rb') as f:
            h = swf.Header.read(f)
            tag = None
            taglist = []
            while not isinstance(tag, tags.End):
                tag = tags.read(h.file)
                if isinstance(tag, tags.DoABC):
                    self.code_headers.append(tag.real_body)
