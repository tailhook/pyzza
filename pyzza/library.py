from weakref import ref

from . import swf, tags, abc

class ClassNotFoundError(Exception):
    pass

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
        with open(filename, 'rb') as f:
            h = swf.Header.read(f)
            tag = None
            taglist = []
            while not isinstance(tag, tags.End):
                tag = tags.read(h.file)
                if isinstance(tag, tags.DoABC):
                    tag.real_body._source = filename
                    self.code_headers.append(tag.real_body)

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
