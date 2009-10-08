from itertools import chain
from operator import methodcaller

from . import parser, library, swf, bytecode, abc, tags

class SyntaxError(Exception): pass
class NameError(SyntaxError): pass

class CodeHeader:
    """
    This class holds structures like those in abc.ABCFile but in more usefull
    format. Method ``make_tag()`` makes it an ``DoABC`` tag, with those cryptic
    ABCFile structure and friends.
    """

    def add_method_body(self, name, frag):
        print('METHOD', name, frag)

    def add_main_script(self, frag):
        print('SCRIPT', frag)

    def make_tag(self):
        tag = abc.DoABC()
        return tag

class NameType:
    pass

class Class(NameType):

    def __init__(self, cls):
        self.cls = cls

    def __repr__(self):
        return '<Class {!r}>'.format(self.cls)

class Register(NameType):

    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return '<R{:d}>'.format(self.value)
        else:
            return '<R:{:x}>'.format(id(self))

class Builtin(NameType):
    pass

class Property(NameType):
    pass

globals = {
    'True': True,
    'False': False,
    'None': None,
    }

class Globals:
    namespace = globals

class CodeFragment:
    """
    Instances of this class contain information about any "method body" in terms
    of actionscript bytecode. Current scope , local variables, bytecodes
    are all here.
    """
    visitors = {
        parser.FromImport: 'import',
        parser.Class: 'class',
        parser.Def: 'function',
        parser.Assign: 'assign',
        parser.Call: 'call',
        str: 'varname',
        parser.String: 'string',
        parser.CallAttr: 'callattr',
        parser.Super: 'super',
        }
    def __init__(self, ast, library, code_header,
            private_namespace,
            class_name=None,
            method_prefix=None,
            parent_namespaces=(Globals(),),
            arguments=(None,),
            ):
        self.library = library
        self.code_header = code_header
        self.bytecodes = [
            bytecode.getlocal_0(),
            bytecode.pushscope(),
            ]
        self.namespace = {}
        self.private_namespace = private_namespace
        self.method_prefix = method_prefix or private_namespace + ':'
        self.class_name = class_name
        self.parent_namespaces = parent_namespaces
        self.arguments = arguments
        for (i, v) in enumerate(arguments):
            self.namespace[v] = Register(i)
        for node in ast:
            self.push_value(node)
        self.bytecodes.append(bytecode.returnvoid())
        from . import pretty
        pretty.pprint(self.bytecodes)

    ##### Utility #####

    def push_value(self, node):
        try:
            visitor = getattr(self, 'visit_'+self.visitors[type(node)])
        except KeyError:
            raise NotImplementedError(node)
        visitor(node)

    def find_name(self, name):
        for ns in chain((self,), self.parent_namespaces):
            if name in ns.namespace:
                break
        else:
            raise NameError(name)
        return ns.namespace[name]

    def get_class(self):
        return self

    ##### Visitors #####

    def visit_import(self, node):
        package = '.'.join(node[0])
        name = node[1]
        cls = self.library.get_class(package, name)
        assert name not in self.namespace
        self.namespace[name] = Class(cls)

    def visit_class(self, node):
        frag = CodeFragment(node.body, self.library, self.code_header,
            private_namespace=self.private_namespace,
            parent_namespaces=(self,) + self.parent_namespaces,
            class_name=node.name)
        self.code_header.add_method_body('', frag)
        assert len(node.bases) <= 1
        val = self.find_name(node.bases[0]).cls
        bases = []
        while val:
            bases.append(val)
            val = val.get_base()
        self.bytecodes.append(bytecode.getscopeobject(0))
        for i in reversed(bases):
            self.bytecodes.append(bytecode.getlex(i))
            self.bytecodes.append(bytecode.pushscope())
        self.bytecodes.append(bytecode.getlex(bases[0]))
        self.bytecodes.append(bytecode.newclass(self.get_class()))
        for i in range(len(bases)):
            self.bytecodes.append(bytecode.popscope())
        self.bytecodes.append(bytecode.initproperty(self.get_class()))

    def visit_function(self, node):
        if self.class_name is not None:
            frag = CodeFragment(node.body, self.library, self.code_header,
                parent_namespaces=(self,) + self.parent_namespaces,
                private_namespace=self.private_namespace,
                arguments=('self',))
        else:
            frag = CodeFragment(node.body, self.library, self.code_header,
                private_namespace=self.private_namespace,
                parent_namespaces=self.parent_namespaces,
                method_prefix=self.method_prefix+self.private_namespace+':')
        self.code_header.add_method_body(self.method_prefix+node.name[0], frag)

    def visit_assign(self, node):
        if isinstance(node[0], str):
            if node[0] not in self.namespace:
                reg = self.namespace[node[0]] = Register()
            else:
                reg = self.namespace[node[0]]
        elif isinstance(node[0], parser.GetAttr):
            self.push_value(node[0][0])
        else:
            raise NotImplementedError(node[0])
        self.push_value(node[1])
        if isinstance(node[0], str):
            self.bytecodes.append(bytecode.setlocal(reg))
        elif isinstance(node[0], parser.GetAttr):
            self.bytecodes.append(bytecode.callproperty(node[0][1][0]))
        else:
            raise NotImplementedError(node[0])

    def visit_call(self, node):
        name = node[0]
        if isinstance(name, str):
            val = self.find_name(name)
            self.bytecodes.append(bytecode.findpropstrict(val))
            if len(node[1]) > 0:
                raise NotImplementedError("No arguments for constructor "
                    "supported")
            self.bytecodes.append(bytecode.constructprop(val, 0))
        else:
            raise NotImplementedError(name)

    def visit_varname(self, node):
        name = node
        for ns in chain((self,), self.parent_namespaces):
            if name in ns.namespace:
                break
        else:
            raise NameError(name)
        val = ns.namespace[name]
        if isinstance(val, bool):
            if val:
                self.bytecodes.append(bytecode.pushtrue())
            else:
                self.bytecodes.append(bytecode.pushfalse())
        elif isinstance(val, Register):
            self.bytecodes.append(bytecode.getlocal(val))
        else:
            raise NotImplementedError(val)

    def visit_string(self, node):
        val = node[0]
        if val[0] == '"':
            assert val[-1] == '"'
            val = val[1:-1]
        elif val[0] == "'":
            assert val[-1] == "'"
            val = val[1:-1]
        else:
            raise NotImplementedError(val)
        self.bytecodes.append(bytecode.pushstring(val))

    def visit_callattr(self, node):
        self.push_value(node[0])
        for i in node[2]:
            self.push_value(i)
        self.bytecodes.append(bytecode.callproperty(node[1], len(node[2])))

    def visit_super(self, node):
        if node[0] == '__init__':
            if len(node[1][0]) > 0:
                raise NotImplementedError("No arguments for super constructor "
                    "supported")
            self.bytecodes.append(bytecode.constructsuper(0))
        else:
            if len(node[1][0]) > 0:
                raise NotImplementedError("No arguments for super call "
                    "supported")
            self.bytecodes.append(bytecode.construct(0))

def get_options():
    import optparse
    op = optparse.OptionParser()
    op.add_option('-l', '--library', metavar="SWFFILE",
        help="Use SWFFILE as library of external classes (repeatable).",
        dest="libraries", default=[], action="append", type="string")
    op.add_option('-o', '--output', metavar="SWFFILE",
        help="Output swf data into SWFFILE.",
        dest="output", default=None, type="string")
    return op

def main():
    global options
    op = get_options()
    options, args = op.parse_args()
    if len(args) != 1:
        op.error("Exacly one argument expected")
    from . import parser, library
    ast = parser.parse_file(args[0])
    lib = library.Library()
    for i in options.libraries:
        lib.add_file(i)
    code_header = CodeHeader()
    frag = CodeFragment(ast, lib, code_header,
        private_namespace=args[0]+'$23')
    code_header.add_method_body('', frag)
    code_header.add_main_script(frag)
    code_tag = code_header.make_tag()
    h = swf.Header()
    content = [
        tags.FileAttributes(),
        code_tag,
        tags.SymbolClass(main_class='Main'),
        tags.ShowFrame(),
        ]
    if options.output:
        out = options.output
    else:
        if args[0].endswith('.py'):
            out = args[0][:-3] + '.swf'
        else:
            out = args[0] + '.swf'
    with open(out, 'wb') as o:
        h.write_swf(o, b''.join(map(methodcaller('blob'), content)))

if __name__ == '__main__':
    from . import compile
    compile.main()
