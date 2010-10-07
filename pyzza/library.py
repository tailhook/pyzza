from weakref import ref
import os.path
import zipfile
from contextlib import closing
import itertools

from . import swf, tags, abc, bytecode

class PropertyNotFoundError(Exception):
    pass
class ClassNotFoundError(PropertyNotFoundError):
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
                names = {}
                for t in tag.real_body.script_info[-1].traits_info:
                    nm = t.name
                    if isinstance(nm.namespace, abc.NSPackage):
                        if isinstance(t.data, abc.TraitClass):
                            names[nm.namespace.name, nm.name] = 'class'
                        elif isinstance(t.data, abc.TraitMethod):
                            names[nm.namespace.name, nm.name] = 'function'
                for t in tag.real_body.class_info:
                    nm = t.instance_info.name
                    if isinstance(nm.namespace, abc.NSPackage):
                        names[nm.namespace.name, nm.name] = 'class'
                tag.real_body._names = names
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
        self._names = {}

    def copy(self):
        res = Library()
        res.code_headers = self.code_headers
        res.class_cache.update(self.class_cache)
        res._names.update(self._names)
        return res

    def add_file(self, filename):
        self.code_headers.extend(LibCache(filename).code_headers)

    def get_property_type(self, package, name):
        for head in itertools.chain((self,), self.code_headers):
            if (package, name) in head._names:
                return head._names[package, name]
        else:
            raise PropertyNotFoundError(package, name)

    def populate_cache(self):
        for head in self.code_headers:
            for (idx, cls) in enumerate(head.class_info):
                qname = cls.instance_info.name
                res = AS3Class(qname, self,
                    class_info=cls,
                    index=idx,
                    header=head,
                    )
                self.class_cache[package, name] = res

    def get_class(self, package, name):
        if (package, name) in self.class_cache:
            return self.class_cache[package, name]
        for head in self.code_headers:
            if (package, name) in head._names:
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
        self._names[name.namespace.name, name.name] = 'class'
        val = self.class_cache[name.namespace.name, name.name] = AS3Class(
            name, self,
            class_info=clsinfo,
            )
        return val

    def add_name(self, package, name, type):
        assert type in ('function', 'class')
        self._names[package, name] = type

    def get_public_names(self):
        for head in self.code_headers:
            for ns, nm in head._names:
                yield ns, nm

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

    @property
    def interface(self):
        return bool(self.class_info.instance_info.flags \
            & abc.InstanceInfo.CONSTANT_ClassInterface)

    def get_base(self):
        lib = self.library()
        sn = self.class_info.instance_info.super_name
        if isinstance(sn, abc.AnyType):
            return None
        return lib.get_class(sn.namespace.name, sn.name)

    def get_method_trait(self, name, raw_trait=False, ignore_ns=False):
        for t in self.class_info.instance_info.trait:
            if isinstance(t.data, abc.TraitMethod) \
                and (t.name == name or ignore_ns and t.name.name == name.name):
                if raw_trait:
                    return t
                else:
                    return t.data
        for t in self.class_info.trait:
            if isinstance(t.data, abc.TraitMethod) \
                and t.name == name:
                if raw_trait:
                    return t
                else:
                    return t.data
