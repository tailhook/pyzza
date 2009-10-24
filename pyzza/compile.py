from itertools import chain, count
from operator import methodcaller, attrgetter
from collections import Counter

from . import parser, library, swf, bytecode, abc, tags

class SyntaxError(Exception): pass
class NameError(SyntaxError): pass
class VerificationError(Exception): pass
class StackError(VerificationError): pass

class CodeHeader:
    """
    This class holds structures like those in abc.ABCFile but in more usefull
    format. Method ``make_tag()`` makes it an ``DoABC`` tag, with those cryptic
    ABCFile structure and friends.
    """

    def __init__(self, filename):
        self.filename = filename
        tag = abc.DoABC()
        tag.flags = 0
        tag.name = self.filename
        tag.empty()
        self.tag = tag

    def add_method_body(self, name, frag):
        mi = abc.MethodInfo()
        mi.param_type = [abc.AnyType() for i in frag.arguments[1:]]
        mi.return_type = abc.AnyType()
        mi.name = name
        mi.flags = 0 # no features supported yet
        self.tag.real_body.method_info.append(mi)
        frag._method_info = mi
        mb = abc.MethodBodyInfo()
        mb.method = mi
        mb.max_stack = frag.max_stack
        mb.local_count = frag.local_count
        mb.init_scope_depth = frag.scope_stack_init
        mb.max_scope_depth = frag.scope_stack_max
        mb.exception_info = []
        mb.traits_info = []
        mb.bytecode = frag.bytecodes
        self.tag.real_body.method_body_info.append(mb)

    def add_class(self, name, bases, frag, package=''):
        cls = abc.ClassInfo()
        inst = abc.InstanceInfo()
        cls.instance_info = inst
        cls.cinit = frag._method_info
        cls.trait = []
        inst.name = abc.QName(abc.NSPackage(package), name)
        inst.super_name = bases[0].name
        inst.flags = 0
        inst.interface = []
        inst.iinit = frag.namespace['__init__'].code_fragment._method_info
        traits = []
        for (k, m) in frag.namespace.items():
            if k == '__init__': continue
            if isinstance(m, Method):
                traits.append(abc.TraitsInfo(
                    abc.QName(abc.NSPackage(package), k),
                    abc.TraitMethod(m.code_fragment._method_info)))
            elif isinstance(m, Register):
                pass #nothing needed
            else:
                raise NotImplementedError(m)
        inst.trait = traits
        self.tag.real_body.class_info.append(cls)
        return cls

    def add_main_script(self, frag):
        script = abc.ScriptInfo()
        script.init = frag._method_info
        script.traits_info = [abc.TraitsInfo(val.class_info.instance_info.name,
                abc.TraitClass(0, val.class_info))
            for (name, val) in frag.namespace.items()
            if isinstance(val, NewClass)]
        self.tag.real_body.script_info.append(script)
        return script

    def make_tag(self):
        return self.tag

##### Name types #####
class NameType:
    """Type of namespace bindings"""

class Class(NameType):
    """Imported class"""
    def __init__(self, cls):
        self.cls = cls

    def __repr__(self):
        return '<Class {!r}>'.format(self.cls)

    @property
    def property_name(self):
        return self.cls.name

class NewClass(NameType):
    """In-source class"""
    def __init__(self, frag, clsinfo):
        self.code_fragment = frag
        self.class_info = clsinfo
        self.cls = frag.library.add_class(clsinfo)

    @property
    def property_name(self):
        return self.class_info.instance_info.name

class Register(NameType):
    """Register reference, can have register number or can have no number"""
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return '<R{:d}>'.format(self.value)
        else:
            return '<R:{:x}>'.format(id(self))

class Builtin(NameType):
    """Some built-in (for global namespace)"""

class Property(NameType):
    """#Don't remember"""

class Method(NameType):
    """Method (for class namespace)"""
    def __init__(self, frag):
        self.code_fragment = frag

class Function(NameType):
    """Function (any def which is not in class namespace)"""
    def __init__(self, frag):
        self.code_fragment = frag

class Builtin(NameType):
    """Pyzza builtins, usually are inline functions"""
    def __init__(self, name):
        self.name = name

##### End Name Types #####

globals = {
    'True': True,
    'False': False,
    'None': None,
    'range': Builtin('range'),
    'keys': Builtin('keys'),
    'items': Builtin('items'),
    'values': Builtin('values'),
    'abs': Builtin('abs'),
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
        parser.ImportStmt: 'import',
        parser.Class: 'class',
        parser.Func: 'function',
        parser.Assign: 'assign',
        parser.Call: 'call',
        parser.Name: 'varname',
        parser.String: 'string',
        parser.CallAttr: 'callattr',
        parser.GetAttr: 'getattr',
        parser.Super: 'super',
        parser.Add: 'add',
        parser.Subtract: 'subtract',
        parser.Multiply: 'multiply',
        parser.Divide: 'divide',
        parser.Modulo: 'modulo',
        parser.Number: 'number',
        parser.Return: 'return',
        parser.If: 'if',
        parser.For: 'for',
        parser.Break: 'break',
        parser.Continue: 'continue',
        parser.Greater: 'greater',
        }
    max_stack = None
    local_count = None
    scope_stack_init = 0 # TODO: fix
    scope_stack_max = 10 # TODO: fix
    def __init__(self, ast, library, code_header,
            private_namespace,
            class_name=None,
            method_prefix=None,
            parent_namespaces=(Globals(),),
            arguments=(None,),
            package_namespace='',
            ):
        self.library = library
        self.code_header = code_header
        self.bytecodes = [
            bytecode.getlocal_0(),
            bytecode.pushscope(),
            ]
        self.namespace = {}
        self.loopstack = [] # pairs of continue label and break label
        self.private_namespace = private_namespace
        self.package_namespace = package_namespace
        self.method_prefix = method_prefix or private_namespace + ':'
        self.class_name = class_name
        self.parent_namespaces = parent_namespaces
        self.arguments = arguments
        for (i, v) in enumerate(arguments):
            self.namespace[v] = Register(i)
        self.exec_suite(ast)
        self.bytecodes.append(bytecode.returnvoid())
        self.fix_registers()
        self.verify_stack()

    ##### Post-processing #####

    def fix_registers(self):
        rcount = Counter()
        for bcode in self.bytecodes:
            for (name, typ, _, _) in bcode.format:
                if issubclass(typ, bytecode.Register):
                    r = getattr(bcode, name)
                    if r.value is None:
                        rcount[r] += 1
        regs = {}
        for (idx, (name, val)) in zip(count(len(self.arguments)), rcount.most_common()):
            regs[name] = idx
        self.local_count = len(self.arguments) + len(regs)
        for bcode in self.bytecodes:
            for (name, typ, _, _) in bcode.format:
                if issubclass(typ, bytecode.Register):
                    rname = getattr(bcode, name)
                    if rname.value is None:
                        rval = regs[rname]
                    else:
                        rval = rname.value
                    setattr(bcode, name, bytecode.Register(rval))

    def verify_stack(self):
        stack_size = 0
        max_stack_size = 0
        for bcode in self.bytecodes:
            if stack_size < len(bcode.stack_before):
                raise StackError("Not enought operands in the stack for "
                    "{!r} (operands: {})".format(bcode, bcode.stack_before))
            if isinstance(bcode, bytecode.Label):
                if hasattr(bcode, '_verify_stack'):
                    if bcode._verify_stack != stack_size:
                        raise StackError("Unbalanced stack at {!r}".format(bcode))
                else:
                    bcode._verify_stack = stack_size
            old_stack = stack_size
            stack_size += len(bcode.stack_after) - len(bcode.stack_before)
            if isinstance(bcode, bytecode.JumpBytecode):
                if hasattr(bcode.offset, '_verify_stack'):
                    if bcode.offset._verify_stack != stack_size:
                        raise StackError("Unbalanced stack at {!r}".format(bcode))
                else:
                    bcode.offset._verify_stack = stack_size
            #print('[{:3d} -{:2d}] {}'.format(old_stack, stack_size, bcode))
            if stack_size > max_stack_size:
                max_stack_size = stack_size
        if stack_size != 0:
            raise StackError("Unbalanced stack at the end of code")
        self.max_stack = max_stack_size

    ##### Utility #####

    def push_value(self, node):
        try:
            visitor = getattr(self, 'visit_'+self.visitors[type(node)])
        except KeyError:
            raise NotImplementedError(node)
        visitor(node, False)

    def execute(self, node):
        try:
            visitor = getattr(self, 'visit_'+self.visitors[type(node)])
        except KeyError:
            raise NotImplementedError(node)
        visitor(node, True)

    def exec_suite(self, suite):
        for line in suite:
            self.execute(line)

    def find_name(self, name):
        for ns in chain((self,), self.parent_namespaces):
            if name in ns.namespace:
                break
        else:
            raise NameError(name)
        return ns.namespace[name]

    ##### Visitors #####

    def visit_import(self, node, void):
        assert void == True
        for name in node.names:
            package = node.module.value
            name = name.value
            cls = self.library.get_class(package, name)
            assert name not in self.namespace
            self.namespace[name] = Class(cls)

    def visit_class(self, node, void):
        assert void == True
        package = ''
        if node.decorators:
            for i in node.decorators:
                if i.name.value == 'package':
                    package = i.arguments[0].value
                else:
                    raise NotImplementedError("No decorator ``{}''".format(i.name))
        frag = CodeFragment(node.body, self.library, self.code_header,
            private_namespace=self.private_namespace,
            parent_namespaces=(self,) + self.parent_namespaces,
            package_namespace=package,
            class_name=node.name.value)
        self.code_header.add_method_body('', frag)
        assert len(node.bases) <= 1
        if not node.bases:
            val = self.library.get_class('', 'Object')
        else:
            val = self.find_name(node.bases[0].value).cls
        bases = []
        while val:
            bases.append(val)
            val = val.get_base()
        cls = self.code_header.add_class(node.name.value, bases, frag,
            package=package)
        self.bytecodes.append(bytecode.getscopeobject(0))
        for i in reversed(bases):
            self.bytecodes.append(bytecode.getlex(i.name))
            self.bytecodes.append(bytecode.pushscope())
        self.bytecodes.append(bytecode.getlex(bases[0].name))
        self.bytecodes.append(bytecode.newclass(cls))
        for i in range(len(bases)):
            self.bytecodes.append(bytecode.popscope())
        self.bytecodes.append(bytecode.initproperty(
            abc.QName(abc.NSPackage(package), node.name.value)))
        self.namespace[node.name.value] = NewClass(frag, cls)

    def visit_function(self, node, void):
        assert void == True
        if self.class_name is not None:
            frag = CodeFragment(node.body, self.library, self.code_header,
                parent_namespaces=(self,) + self.parent_namespaces,
                private_namespace=self.private_namespace,
                arguments=list(map(attrgetter('value'), node.arguments)))
            self.namespace[node.name.value] = Method(frag)
        else:
            frag = CodeFragment(node.body, self.library, self.code_header,
                private_namespace=self.private_namespace,
                parent_namespaces=self.parent_namespaces,
                method_prefix=self.method_prefix+self.private_namespace+':')
            self.namespace[node.name[0]] = Function(frag)
        self.code_header.add_method_body(self.method_prefix+node.name.value, frag)

    def visit_assign(self, node, void):
        assert void == True
        if isinstance(node.target, parser.Name):
            if node.target.value not in self.namespace:
                reg = self.namespace[node.target.value] = Register()
            else:
                reg = self.namespace[node[0]]
            if node.operator.value != '=':
                self.bytecodes.append(bytecode.getlocal(reg))
        elif isinstance(node.target, parser.GetAttr):
            self.push_value(node.target.expr)
            if node.operator.value != '=':
                self.bytecodes.append(bytecode.dup())
                self.bytecodes.append(bytecode.getproperty(
                    abc.QName(abc.NSPackage(self.package_namespace),
                    node.target.name.value)))
        else:
            raise NotImplementedError(node.target)
        self.push_value(node.expr)
        if isinstance(node.target, parser.Name):
            if node.operator.value == '=':
                pass
            elif node.operator.value == '+=':
                self.bytecodes.append(bytecode.add())
            else:
                raise NotImplementedError(node.operator)
            self.bytecodes.append(bytecode.setlocal(reg))
        elif isinstance(node.target, parser.GetAttr):
            if node.operator.value == '=':
                pass
            elif node.operator.value == '+=':
                self.bytecodes.append(bytecode.add())
            else:
                raise NotImplementedError(node.operator)
            self.bytecodes.append(bytecode.setproperty(
                abc.QName(abc.NSPackage(self.package_namespace),
                node.target.name.value)))
        else:
            raise NotImplementedError(node.target)

    def visit_call(self, node, void):
        name = node.expr
        if isinstance(name, parser.Name):
            name = name.value
            val = self.find_name(name)
            self.bytecodes.append(bytecode.findpropstrict(val.property_name))
            for i in node.arguments:
                self.push_value(i)
            self.bytecodes.append(bytecode.constructprop(val.property_name,
                len(node.arguments)))
            if void:
                self.bytecodes.append(bytecode.pop())
        else:
            raise NotImplementedError(name)

    def visit_varname(self, node, void):
        if void: return
        name = node.value
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
        elif isinstance(val, Class):
            self.bytecodes.append(bytecode.getlex(
                val.cls.name))
        else:
            raise NotImplementedError(val)

    def visit_string(self, node, void):
        if void: return
        self.bytecodes.append(bytecode.pushstring(node.value))

    def visit_number(self, node, void):
        if void: return
        if isinstance(node.value, float):
            self.bytecodes.append(bytecode.pushdouble(node.value))
        elif isinstance(node.value, int):
            if node.value < 256:
                self.bytecodes.append(bytecode.pushbyte(node.value))
            elif node.value < 65536:
                self.bytecodes.append(bytecode.pushshort(node.value))
            else:
                self.bytecodes.append(bytecode.pushinteger(node.value))
        else:
            raise NotImplementedError(node)

    def visit_callattr(self, node, void):
        self.push_value(node.expr)
        for i in node.arguments:
            self.push_value(i)
        if void:
            self.bytecodes.append(bytecode.callpropvoid(
                abc.QName(abc.NSPackage(''), node.attribute.value),
                len(node.arguments)))
        else:
            self.bytecodes.append(bytecode.callproperty(
                abc.QName(abc.NSPackage(''), node.attribute.value),
                len(node.arguments)))

    def visit_getattr(self, node, void):
        if void: return
        self.push_value(node.expr)
        self.bytecodes.append(bytecode.getproperty(
            abc.QName(abc.NSPackage(''), node.name.value)))

    def visit_super(self, node, void):
        if node.method.value == '__init__':
            assert void == True
            self.bytecodes.append(bytecode.getlocal_0())
            for i in node.arguments:
                self.push_value(i)
            self.bytecodes.append(bytecode.constructsuper(len(node.arguments)))
        else:
            raise NotImplementedError()

    ##### Flow control #####

    def visit_if(self, node, void):
        assert void == True
        endlabel = bytecode.Label()
        for (cond, suite) in node.ifs:
            self.push_value(cond)
            lab = bytecode.Label()
            self.bytecodes.append(bytecode.iffalse(lab))
            self.exec_suite(suite)
            self.bytecodes.append(bytecode.jump(endlabel))
            self.bytecodes.append(lab)
        if node.else_:
            self.exec_suite(node.else_)
        self.bytecodes.append(endlabel)

    def visit_for(self, node, void):
        assert void == True
        endlabel = bytecode.Label()
        if isinstance(node.expr, parser.Call) \
            and isinstance(node.expr.expr, parser.Name):
            val = self.find_name(node.expr.expr.value)
            if isinstance(val, Builtin):
                if val.name == 'range':
                    if len(node.expr.arguments) < 2:
                        assert len(node.var) == 1, node.var
                        reg = self.namespace[node.var[0].value] = Register()
                        amountreg = Register()
                        bodylab = bytecode.label()
                        contlab = bytecode.Label()
                        condlab = bytecode.Label()
                        self.push_value(node.expr.arguments[0])
                        self.bytecodes.append(bytecode.setlocal(amountreg))
                        self.bytecodes.append(bytecode.pushbyte(0))
                        self.bytecodes.append(bytecode.setlocal(reg))
                        self.bytecodes.append(bytecode.jump(condlab))
                        self.bytecodes.append(bodylab)
                        self.loopstack.append((contlab, endlabel))
                        self.exec_suite(node.body)
                        self.loopstack.pop()
                        self.bytecodes.append(contlab)
                        self.bytecodes.append(bytecode.getlocal(reg))
                        self.bytecodes.append(bytecode.increment_i())
                        self.bytecodes.append(bytecode.setlocal(reg))
                        self.bytecodes.append(condlab)
                        self.bytecodes.append(bytecode.getlocal(reg))
                        self.bytecodes.append(bytecode.getlocal(amountreg))
                        self.bytecodes.append(bytecode.iflt(bodylab))
                    else:
                        raise NotImplementedError()
                else:
                    raise NotImplementedError(val.name)
            else:
                raise NotImplementedError(node.expr.expr)
        else:
            raise NotImplementedError(node.expr)
        if node.else_:
            self.exec_suite(node.else_)
        self.bytecodes.append(endlabel)

    def visit_return(self, node, void):
        assert void == True
        self.push_value(node.expr)
        self.bytecodes.append(bytecode.returnvalue())

    def visit_break(self, node, void):
        assert void == True
        self.bytecodes.append(bytecode.jump(self.loopstack[-1][1]))

    def visit_continue(self, node, void):
        assert void == True
        self.bytecodes.append(bytecode.jump(self.loopstack[-1][0]))

    ##### Math #####

    def visit_add(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            self.bytecodes.append(bytecode.add())

    def visit_subtract(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            self.bytecodes.append(bytecode.subtract())

    def visit_multiply(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            self.bytecodes.append(bytecode.multiply())

    def visit_divide(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            self.bytecodes.append(bytecode.divide())

    def visit_modulo(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            self.bytecodes.append(bytecode.modulo())

    def visit_greater(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            self.bytecodes.append(bytecode.greaterthan())

def get_options():
    import optparse
    op = optparse.OptionParser()
    op.add_option('-l', '--library', metavar="SWFFILE",
        help="Use SWFFILE as library of external classes (repeatable).",
        dest="libraries", default=[], action="append", type="string")
    op.add_option('-n', '--no-std-globals',
        help="Do not add standart globals to a namespace (e.g. if you "
            "don't use library.swf from playerglobal.swc as a library)",
        dest="std_globals", default=True, action="store_false")
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
    ast = parser.parser().parse_file(args[0])
    lib = library.Library()
    for i in options.libraries:
        lib.add_file(i)
    if options.std_globals:
        globals['Math'] = Class(lib.get_class('', 'Math'))
    code_header = CodeHeader(args[0])
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
