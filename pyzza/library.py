from weakref import ref
import os.path
import zipfile
from contextlib import closing

from . import swf, tags, abc, bytecode

class ClassNotFoundError(Exception):
    pass

def get_public_names(filename):
    lib = Library()
    lib.add_file(filename)
    return lib.get_public_names()

class LibCache:
    files = {}
    def __new__(C, filename):
        if filename in C.files:
            res = C.files[filename]
            if res.mtime == os.path.getmtime(filename):
                return
        return object.__new__(C)

    def __init__(self, filename):
        self.code_headers = []
        if filename.endswith('.swc'):
            zip = zipfile.ZipFile(filename)
            for finfo in zip.filelist:
                if finfo.filename.endswith('.swf'):
                    with closing(zip.open(finfo.filename)) as ff:
                        self._read(ff, filename + ':' + finfo.filename)
        else:
            with open(filename, 'rb') as f:
                self._read(f, filename)


    def _read(self, file, filename):
        h = swf.Header.read(file)
        tag = None
        taglist = []
        while not isinstance(tag, tags.End):
            tag = tags.read(h.file)
            if isinstance(tag, tags.DoABC):
                tag.real_body._source = filename
                self.code_headers.append(tag.real_body)


class Library:
    """
    This class holds a reference to all ABCFile structures of all files loaded
    as a library. So that subclasses can find out correct scope, method
    signatures and property namespaces can be checked, and some small methods
    can be inlined.
    """

    def __init__(self):
        self.code_headers = []
        self.class_cache = {}

    def add_file(self, filename):
        self.code_headers.extend(LibCache(filename).code_headers)

    def get_class(self, package, name):
        if (package, name) in self.class_cache:
            return self.class_cache[package, name]
        for head in self.code_headers:
            for (idx, cls) in enumerate(head.class_info):
                qname = cls.instance_info.name
                if name == qname.name and qname.namespace.name == package:
                    res = AS3Class(qname, self,
                        class_info=cls,
                        index=idx,
                        header=head,
                        )
                    self.class_cache[package, name] = res
                    return res
        else:
            raise ClassNotFoundError(package, name)

    def add_class(self, clsinfo):
        name = clsinfo.instance_info.name
        val = self.class_cache[name.namespace.name, name.name] = AS3Class(
            name, self,
            class_info=clsinfo,
            )
        return val

    def get_public_names(self):
        for head in self.code_headers:
            for cls in head.class_info:
                name = cls.instance_info.name
                yield name.namespace.name, name.name

class AS3Class:

    def __init__(self, qname, lib, class_info, header=None, index=None):
        self.name = qname
        self.library = ref(lib)
        self.class_info = class_info
        self.header = header
        self.index = index

    def __repr__(self):
        return '<{} {}:{} from {}:{}>'.format(self.__class__.__name__,
            self.name.namespace.name, self.name.name,
            self.header and self.header._source, self.index)

    def get_base(self):
        lib = self.library()
        sn = self.class_info.instance_info.super_name
        if isinstance(sn, abc.AnyType):
            return None
        return lib.get_class(sn.namespace.name, sn.name)

    def has_method(self, name):
        for t in self.class_info.instance_info.trait:
            if isinstance(t.data, abc.TraitMethod) \
                and t.name.name == name:
                return True
