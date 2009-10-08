from weakref import ref

from . import swf, tags

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
            return self.class_cache
        for head in self.code_headers:
            for (idx, inst) in enumerate(head.instance_info):
                qname = head.constant_pool.multiname_info[inst.name-1]
                cname = head.constant_pool.string[qname.name-1]
                ns = head.constant_pool.namespace_info[qname.ns-1]
                nsname = head.constant_pool.string[ns.name-1]
                if cname == name and nsname == package:
                    res = AS3Class(package, name, self,
                        index=idx,
                        header=head,
                        )
                    self.class_cache[package, name] = res
                    return res
        else:
            raise ClassNotFoundError(package, name)

class AS3Class:

    def __init__(self, package, name, lib, header, index):
        self.package = package
        self.name = name
        self.library = ref(lib)
        self.header = header
        self.index = index

    def __repr__(self):
        return '<{} {}:{} from {}:{}>'.format(self.__class__.__name__,
            self.package, self.name,
            self.header._source, self.index)

    def get_base(self):
        lib = self.library()
        sn = self.header.instance_info[self.index].super_name
        if not sn:
            return None
        qname = self.header.constant_pool.multiname_info[sn-1]
        cname = self.header.constant_pool.string[qname.name-1]
        ns = self.header.constant_pool.namespace_info[qname.ns-1]
        nsname = self.header.constant_pool.string[ns.name-1]
        return lib.get_class(nsname, cname)


