from itertools import chain, count
from operator import methodcaller, attrgetter
from collections import Counter
from contextlib import contextmanager

from . import parser, library, swf, bytecode, abc, tags

class SyntaxError(Exception): pass
class NameError(SyntaxError): pass
class VerificationError(Exception): pass
class StackError(VerificationError): pass

def binary(fun):
    def wrapper(self, node, void):
        if void:
            self.execute(node.left)
            self.execute(node.right)
        else:
            self.push_value(node.left)
            self.push_value(node.right)
            fun(self, node)
    return wrapper

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
        mi.flags = 0
        if hasattr(frag, 'activation'):
            mi.flags |= abc.MethodInfo.NEED_ACTIVATION
        self.tag.real_body.method_info.append(mi)
        frag._method_info = mi
        mb = abc.MethodBodyInfo()
        mb.method = mi
        mb.max_stack = frag.max_stack
        mb.local_count = frag.local_count
        mb.init_scope_depth = frag.scope_stack_init
        mb.max_scope_depth = frag.scope_stack_max
        mb.exception_info = frag.exceptions
        traits = []
        for (k, v) in frag.namespace.items():
            if isinstance(v, ClosureSlot):
                traits.append(abc.TraitsInfo(
                    abc.QName(abc.NSInternal(), k),
                    abc.TraitSlot(v.index),
                    attr=0))
        mb.traits_info = traits
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
                flag = 0
                for b in bases:
                    if b.has_method(k):
                        flag = abc.TraitsInfo.ATTR_Override
                        break
                traits.append(abc.TraitsInfo(
                    abc.QName(abc.NSPackage(package), k),
                    abc.TraitMethod(m.code_fragment._method_info),
                    attr=flag))
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

class ClosureSlot(NameType):
    """Closure variable"""
    def __init__(self, idx, name):
        self.index = idx
        self.name = name

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
    'undefined': abc.Undefined(),
    'range': Builtin('range'),
    'keys': Builtin('keys'),
    'items': Builtin('items'),
    'values': Builtin('values'),
    'abs': Builtin('abs'),
    }

class Globals:
    namespace = globals

class NameCheck:
    visitors = {
        parser.Func: 'function',
        parser.Class: 'class',
        parser.Assign: 'assign',
        parser.For: 'for',
        parser.Try: 'try',
        parser.Name: 'varname',
        parser.GetAttr: 'getattr',
        parser.CallAttr: 'callattr',
        parser.Super: 'super',
        }

    def __init__(self, node):
        self.allnames = set()
        if hasattr(node, 'arguments'):
            self.localnames = set(map(attrgetter('value'), node.arguments))
        else:
            self.localnames = set()
        self.functions = []
        for n in (node.body if hasattr(node, 'body') else node):
            assert n is not None, node
            self.visit(n)
        self.annotate(node)

    def annotate(self, node):
        exvars = set()
        for f in self.functions:
            exvars.update(f.func_globals & self.localnames)
        node.func_export = frozenset(exvars)
        node.func_locals = frozenset(self.localnames)
        node.func_globals = frozenset(self.allnames - self.localnames)
        #~ print(getattr(node, 'name', None),
            #~ node.func_globals, node.func_locals, node.func_export)

    def visit_function(self, node):
        NameCheck(node)
        self.localnames.add(node.name.value)
        self.functions.append(node)

    def visit_class(self, node):
        NameCheck(node)
        self.functions.append(node)

    def visit_getattr(self, node):
        self.visit(node.expr)

    def visit_callattr(self, node):
        self.visit(node.expr)
        for a in node.arguments:
            self.visit(a)

    def visit_super(self, node):
        for a in node.arguments:
            self.visit(a)

    def visit_assign(self, node):
        if isinstance(node.target, parser.Name):
            self.localnames.add(node.target.value)
        for n in node:
            self.visit(n)

    def visit_for(self, node):
        for v in node.var:
            if isinstance(v, parser.Name):
                self.localnames.add(v.value)
            else:
                raise NotImplementedError(v)
        for n in node:
            self.visit(n)

    def visit_try(self, node):
        for (t, v, b) in node.excepts:
            if v is None:
                pass
            elif isinstance(v, parser.Name):
                self.localnames.add(v.value)
            else:
                raise NotImplementedError(v)
        for n in node:
            self.visit(n)

    def visit_varname(self, node):
        self.allnames.add(node.value)

    def visit(self, node):
        try:
            visitor = self.visitors[type(node)]
        except KeyError:
            try:
                ch = iter(node)
            except AttributeError:
                pass # leaf node
            else:
                for n in node:
                    assert n is not None, node
                    self.visit(n)
        else:
            getattr(self, 'visit_' + visitor)(node)


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
        parser.Subscr: 'subscr',
        parser.Super: 'super',
        parser.Add: 'add',
        parser.Subtract: 'subtract',
        parser.Multiply: 'multiply',
        parser.Divide: 'divide',
        parser.Modulo: 'modulo',
        parser.Number: 'number',
        parser.Return: 'return',
        parser.Raise: 'raise',
        parser.If: 'if',
        parser.For: 'for',
        parser.While: 'while',
        parser.Try: 'try',
        parser.Break: 'break',
        parser.Continue: 'continue',
        parser.Greater: 'greater',
        parser.GreaterEq: 'greatereq',
        parser.Less: 'less',
        parser.LessEq: 'lesseq',
        parser.Equal: 'equal',
        parser.NotEqual: 'notequal',
        parser.NotTest: 'not',
        parser.Or: 'or',
        parser.And: 'and',
        parser.Negate: 'negate',
        parser.ListMaker: 'list',
        parser.DictMaker: 'dict',
        }
    max_stack = None
    local_count = None
    scope_stack_init = 0 # TODO: fix
    scope_stack_max = 10 # TODO: fix
    def __init__(self, ast, library, code_header,
            private_namespace,
            class_name=None,
            parent_namespaces=(Globals(),),
            arguments=(None,),
            package_namespace='',
            filename=None,
            ):
        self.library = library
        self.code_header = code_header
        self.bytecodes = [
            bytecode.debugfile(filename),
            bytecode.debugline(getattr(ast, 'lineno', 0)),
            bytecode.getlocal_0(),
            bytecode.pushscope(),
            ]
        self.namespace = {k: Register() for k in ast.func_locals
            if k not in ast.func_export}
        if ast.func_export:
            self.activation = Register()
            self.bytecodes.append(bytecode.newactivation())
            self.bytecodes.append(bytecode.dup())
            self.bytecodes.append(bytecode.pushscope())
            self.bytecodes.append(bytecode.setlocal(self.activation))
            self.namespace.update((k, ClosureSlot(idx+1, k))
                for (idx, k) in enumerate(ast.func_export))
        self.loopstack = [] # pairs of continue label and break label
        self.exceptions = []
        self.private_namespace = private_namespace
        self.package_namespace = package_namespace
        self.class_name = class_name
        self.parent_namespaces = parent_namespaces
        self.arguments = arguments
        self.filename = filename
        self.current_line = None
        for (i, v) in enumerate(arguments):
            if v in ast.func_export:
                self.bytecodes.append(bytecode.getlocal(
                    self.activation))
                self.bytecodes.append(bytecode.getlocal(Register(i)))
                self.bytecodes.append(bytecode.setslot(self.namespace[v].index))
            else:
                self.namespace[v] = Register(i)
        self.exec_suite(ast.body if hasattr(ast, 'body') else ast)
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
            #~ print('[{:3d} -{:2d}] {}'.format(old_stack, stack_size, bcode))
            if stack_size > max_stack_size:
                max_stack_size = stack_size
        if stack_size != 0:
            raise StackError("Unbalanced stack at the end of code")
        self.max_stack = max_stack_size

    ##### Utility #####

    def push_value(self, node):
        self.execute(node, False)

    def execute(self, node, void=True):
        oldline = self.current_line
        if self.current_line != node.lineno:
            self.bytecodes.append(bytecode.debugline(node.lineno))
            self.current_line = node.lineno
        try:
            visitor = getattr(self, 'visit_'+self.visitors[type(node)])
        except KeyError:
            raise NotImplementedError(node)
        else:
            visitor(node, void)
        finally:
            self.current_line = oldline

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

    def qname(self, name):
        return abc.QName(abc.NSPackage(self.package_namespace), name)

    def qintern(self, name):
        return abc.QName(abc.NSInternal(), name)

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
        frag = CodeFragment(node, self.library, self.code_header,
            private_namespace=self.private_namespace,
            parent_namespaces=(self,) + self.parent_namespaces,
            package_namespace=package,
            class_name=node.name.value,
            filename=self.filename,
            )
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
            self.qname(node.name.value)))
        self.namespace[node.name.value] = NewClass(frag, cls)

    def visit_function(self, node, void):
        assert void == True
        if self.class_name is not None:
            frag = CodeFragment(node, self.library, self.code_header,
                parent_namespaces=self.parent_namespaces,
                private_namespace=self.private_namespace,
                arguments=list(map(attrgetter('value'), node.arguments)),
                filename=self.filename,
                )
            self.namespace[node.name.value] = Method(frag)
            self.code_header.add_method_body(
                '{}/{}'.format(self.class_name, node.name.value),
                frag)
        else:
            frag = CodeFragment(node, self.library, self.code_header,
                private_namespace=self.private_namespace,
                parent_namespaces=(self,) + self.parent_namespaces,
                arguments=[None] + list(
                    map(attrgetter('value'), node.arguments)),
                filename=self.filename,
                )
            reg = self.namespace[node.name.value]
            self.code_header.add_method_body('{}${:d}:{}'.format(self.filename,
                node.lineno, node.name.value),
                frag)
            self.bytecodes.append(bytecode.newfunction(frag._method_info))
            self.bytecodes.append(bytecode.coerce_a())
            self.bytecodes.append(bytecode.setlocal(reg))

    @contextmanager
    def assign(self, target, _swap=False):
        if isinstance(target, parser.Name):
            reg = self.namespace[target.value]
            if isinstance(reg, ClosureSlot):
                self.bytecodes.append(bytecode.getlocal(self.activation))
                if _swap:
                    self.bytecodes.append(bytecode.swap())
        elif isinstance(target, parser.GetAttr):
            self.push_value(target.expr)
            if _swap:
                self.bytecodes.append(bytecode.swap())
        elif isinstance(target, parser.Subscr):
            self.push_value(target.expr)
            self.push_value(target.index)
            if _swap:
                raise NotImplementedError(target)
        else:
            raise NotImplementedError(target)
        try:
            yield
        finally:
            if isinstance(target, parser.Name):
                self.bytecodes.append(bytecode.coerce_a())
                if isinstance(reg, Register):
                    self.bytecodes.append(bytecode.setlocal(reg))
                elif isinstance(reg, ClosureSlot):
                    self.bytecodes.append(bytecode.setslot(reg.index))
                else:
                    raise NotImplementedError(reg)
            elif isinstance(target, parser.GetAttr):
                self.bytecodes.append(bytecode.setproperty(
                    self.qname(target.name.value)))
            elif isinstance(target, parser.Subscr):
                self.bytecodes.append(bytecode.setproperty(
                    abc.MultinameL(abc.NamespaceSetInfo(abc.NSPackage('')))))
            else:
                raise NotImplementedError(target)

    def do_assign(self, target):
        with self.assign(target, _swap=True):
            pass

    def visit_assign(self, node, void):
        assert void == True
        with self.assign(node.target):
            if node.operator.value != '=':
                if isinstance(node.target, parser.Name):
                    reg = self.namespace[node.target.value]
                    if isinstance(reg, Register):
                        self.bytecodes.append(bytecode.getlocal(reg))
                    elif isinstance(reg, ClosureSlot):
                        self.bytecodes.append(bytecode.dup())
                        self.bytecodes.append(bytecode.getslot(reg.index))
                    else:
                        raise NotImplementedError(reg)
                elif isinstance(node.target, parser.GetAttr):
                    self.bytecodes.append(bytecode.dup())
                    self.bytecodes.append(bytecode.getproperty(
                        self.qname(node.target.name.value)))
                else:
                    raise NotImplementedError(node.target)
            self.push_value(node.expr)
            if node.operator.value == '=':
                pass
            elif node.operator.value == '+=':
                self.bytecodes.append(bytecode.add())
            elif node.operator.value == '-=':
                self.bytecodes.append(bytecode.subtract())
            elif node.operator.value == '*=':
                self.bytecodes.append(bytecode.multiply())
            elif node.operator.value == '/=':
                self.bytecodes.append(bytecode.divide())
            elif node.operator.value == '%=':
                self.bytecodes.append(bytecode.modulo())
            else:
                raise NotImplementedError(node.operator)

    def visit_call(self, node, void):
        name = node.expr
        if isinstance(name, parser.Name):
            name = name.value
            val = self.find_name(name)
            if isinstance(val, (Class, NewClass)):
                self.bytecodes.append(bytecode.findpropstrict(val.property_name))
                for i in node.arguments:
                    self.push_value(i)
                self.bytecodes.append(bytecode.constructprop(val.property_name,
                    len(node.arguments)))
                if void:
                    self.bytecodes.append(bytecode.pop())
            elif isinstance(val, Register):
                self.bytecodes.append(bytecode.getlocal(val))
                self.bytecodes.append(bytecode.pushnull())
                for i in node.arguments:
                    self.push_value(i)
                self.bytecodes.append(bytecode.call(len(node.arguments)))
                if void:
                    self.bytecodes.append(bytecode.pop())
            else:
                raise NotImplementedError(val)
        else:
            self.push_value(node.expr)
            self.bytecodes.append(bytecode.pushnull())
            for i in node.arguments:
                self.push_value(i)
            self.bytecodes.append(bytecode.call(len(node.arguments)))
            if void:
                self.bytecodes.append(bytecode.pop())

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
            assert ns is self
            self.bytecodes.append(bytecode.getlocal(val))
        elif isinstance(val, ClosureSlot):
            if val.name in self.namespace:
                self.bytecodes.append(bytecode.getlocal(self.activation))
                self.bytecodes.append(bytecode.getslot(val.index))
            else:
                self.bytecodes.append(bytecode.getlex(self.qintern(val.name)))
        elif isinstance(val, Class):
            self.bytecodes.append(bytecode.getlex(
                val.cls.name))
        elif val is None:
            self.bytecodes.append(bytecode.pushnull())
        elif val is abc.Undefined():
            self.bytecodes.append(bytecode.pushundefined())
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
                self.qname(node.attribute.value),
                len(node.arguments)))
        else:
            self.bytecodes.append(bytecode.callproperty(
                self.qname(node.attribute.value),
                len(node.arguments)))

    def visit_getattr(self, node, void):
        if void: return
        self.push_value(node.expr)
        self.bytecodes.append(bytecode.getproperty(self.qname(node.name.value)))

    def visit_subscr(self, node, void):
        if void: return
        self.push_value(node.expr)
        self.push_value(node.index)
        self.bytecodes.append(bytecode.getproperty(
            abc.MultinameL(abc.NamespaceSetInfo(abc.NSPackage('')))))

    def visit_super(self, node, void):
        if node.method.value == '__init__':
            assert void == True
            self.bytecodes.append(bytecode.getlocal_0())
            for i in node.arguments:
                self.push_value(i)
            self.bytecodes.append(bytecode.constructsuper(len(node.arguments)))
        else:
            self.bytecodes.append(bytecode.getlocal_0())
            for i in node.arguments:
                self.push_value(i)
            if void:
                self.bytecodes.append(bytecode.callsupervoid(
                    self.qname(node.method.value),
                    len(node.arguments)))
            else:
                self.bytecodes.append(bytecode.callsuper(
                    self.qname(node.method.value),
                    len(node.arguments)))

    def visit_list(self, node, void):
        if void:
            for i in node:
                self.execute(i)
        else:
            for i in node:
                self.push_value(i)
            self.bytecodes.append(bytecode.newarray(len(node)))

    def visit_dict(self, node, void):
        if void:
            for i in node:
                self.execute(i)
        else:
            assert len(node) % 2 == 0, node
            for i in node:
                self.push_value(i)
            self.bytecodes.append(bytecode.newobject(len(node)//2))

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
        elselabel = bytecode.Label()
        if isinstance(node.expr, parser.Call) \
            and isinstance(node.expr.expr, parser.Name):
            val = self.find_name(node.expr.expr.value)
            if isinstance(val, Builtin):
                if val.name == 'range':
                    if len(node.expr.arguments) < 2:
                        start = parser.Number('0', ('',(node.expr.lineno,
                            node.expr.col)))
                        step = 1
                        stop = node.expr.arguments[0]
                    else:
                        start = node.expr.arguments[0]
                        stop = node.expr.arguments[1]
                        if len(node.expr.arguments) > 2:
                            assert len(node.expr.arguments) == 3, node.expr
                            step = node.expr.arguments[2]
                            if isinstance(step, parser.Number)\
                                and step.value == 1:
                                step = 1
                        else:
                            step = 1
                    assert len(node.var) == 1, node.var
                    stepreg = Register()
                    iterreg = Register()
                    stopreg = Register()
                    bodylab = bytecode.label()
                    contlab = bytecode.Label()
                    condlab = bytecode.Label()
                    self.push_value(start)
                    self.bytecodes.append(bytecode.convert_i())
                    self.bytecodes.append(bytecode.setlocal(iterreg))
                    self.push_value(stop)
                    self.bytecodes.append(bytecode.convert_i())
                    self.bytecodes.append(bytecode.setlocal(stopreg))
                    if step != 1:
                        self.push_value(step)
                        self.bytecodes.append(bytecode.convert_i())
                        self.bytecodes.append(bytecode.setlocal(stepreg))
                    self.bytecodes.append(bytecode.jump(condlab))
                    self.bytecodes.append(bodylab)
                    with self.assign(node.var[0]):
                        self.bytecodes.append(bytecode.getlocal(iterreg))
                    self.loopstack.append((contlab, endlabel))
                    self.exec_suite(node.body)
                    self.loopstack.pop()
                    self.bytecodes.append(contlab)
                    self.bytecodes.append(bytecode.debugline(node.lineno))
                    self.bytecodes.append(bytecode.getlocal(iterreg))
                    if step == 1:
                        self.bytecodes.append(bytecode.increment_i())
                    else:
                        self.bytecodes.append(bytecode.getlocal(stepreg))
                        self.bytecodes.append(bytecode.add_i())
                    self.bytecodes.append(bytecode.setlocal(iterreg))
                    self.bytecodes.append(condlab)
                    self.bytecodes.append(bytecode.debugline(node.lineno))
                    if step == 1 or isinstance(step, parser.Number):
                        self.bytecodes.append(bytecode.getlocal(iterreg))
                        self.bytecodes.append(bytecode.getlocal(stopreg))
                        if step == 1 or step.value > 0:
                            self.bytecodes.append(bytecode.iflt(bodylab))
                        elif step.value < 0:
                            self.bytecodes.append(bytecode.ifgt(bodylab))
                        else:
                            raise NotImplementedError('Zero range step value')
                    else:
                        neglab = bytecode.Label()
                        self.bytecodes.append(bytecode.pushbyte(0))
                        self.bytecodes.append(bytecode.getlocal(stepreg))
                        self.bytecodes.append(bytecode.ifgt(neglab))
                        self.bytecodes.append(bytecode.getlocal(iterreg))
                        self.bytecodes.append(bytecode.getlocal(stopreg))
                        self.bytecodes.append(bytecode.iflt(bodylab))
                        self.bytecodes.append(bytecode.jump(elselabel))
                        self.bytecodes.append(neglab)
                        self.bytecodes.append(bytecode.getlocal(iterreg))
                        self.bytecodes.append(bytecode.getlocal(stopreg))
                        self.bytecodes.append(bytecode.ifgt(bodylab))
                elif val.name in ('keys', 'items', 'values'):
                    assert len(node.expr.arguments) == 1, node.expr
                    obj = Register()
                    idx = Register()
                    contlabel = bytecode.Label()
                    bodylabel = bytecode.label()
                    self.push_value(node.expr.arguments[0])
                    self.bytecodes.append(bytecode.setlocal(obj))
                    self.bytecodes.append(bytecode.pushbyte(0))
                    self.bytecodes.append(bytecode.setlocal(idx))
                    self.bytecodes.append(bytecode.jump(contlabel))
                    self.bytecodes.append(bodylabel)
                    if val.name == 'keys':
                        assert len(node.var) == 1
                        with self.assign(node.var[0]):
                            self.bytecodes.append(bytecode.getlocal(obj))
                            self.bytecodes.append(bytecode.getlocal(idx))
                            self.bytecodes.append(bytecode.nextname())
                    elif val.name == 'values':
                        assert len(node.var) == 1
                        with self.assign(node.var[0]):
                            self.bytecodes.append(bytecode.getlocal(obj))
                            self.bytecodes.append(bytecode.getlocal(idx))
                            self.bytecodes.append(bytecode.nextvalue())
                    elif val.name == 'items':
                        assert len(node.var) == 2
                        with self.assign(node.var[0]):
                            self.bytecodes.append(bytecode.getlocal(obj))
                            self.bytecodes.append(bytecode.getlocal(idx))
                            self.bytecodes.append(bytecode.nextname())
                        with self.assign(node.var[1]):
                            self.bytecodes.append(bytecode.getlocal(obj))
                            self.bytecodes.append(bytecode.getlocal(idx))
                            self.bytecodes.append(bytecode.nextvalue())
                    self.loopstack.append((contlabel, endlabel))
                    self.exec_suite(node.body)
                    self.loopstack.pop()
                    self.bytecodes.append(contlabel)
                    self.bytecodes.append(bytecode.hasnext2(obj, idx))
                    self.bytecodes.append(bytecode.iftrue(bodylabel))
                else:
                    raise NotImplementedError(val.name)
            else:
                raise NotImplementedError(node.expr.expr)
        else:
            raise NotImplementedError(node.expr)
        self.bytecodes.append(elselabel)
        if node.else_:
            self.exec_suite(node.else_)
        self.bytecodes.append(endlabel)

    def visit_while(self, node, void):
        assert void == True
        endlabel = bytecode.Label()
        contlab = bytecode.label()
        elselab = bytecode.Label()
        self.bytecodes.append(contlab)
        self.push_value(node.condition)
        self.bytecodes.append(bytecode.iffalse(elselab))
        self.loopstack.append((contlab, endlabel))
        self.exec_suite(node.body)
        self.loopstack.pop()
        self.bytecodes.append(bytecode.jump(contlab))
        self.bytecodes.append(elselab)
        if node.else_:
            self.exec_suite(node.else_)
        self.bytecodes.append(endlabel)

    def visit_try(self, node, void):
        assert void
        startlabel = bytecode.Label()
        endbodylabel = bytecode.Label()
        elselabel = bytecode.Label()
        endlabel = bytecode.Label()

        self.bytecodes.append(startlabel)
        self.exec_suite(node.body)
        self.bytecodes.append(endbodylabel)
        self.bytecodes.append(bytecode.jump(elselabel))
        for exc in node.excepts + [node.except_]:
            if not exc: continue
            catchlabel = bytecode.Label()
            excinfo = abc.ExceptionInfo()
            excinfo.exc_from = startlabel
            excinfo.exc_to = endbodylabel
            excinfo.target = catchlabel
            variable = None
            if isinstance(exc, tuple):
                excinfo.exc_type = self.find_name(exc[0].value).cls.name
                if exc[1] is not None:
                    excinfo.var_name = self.qname(exc[1].value)
                    variable = exc[1]
                else:
                    excinfo.var_name = None
                excbody = exc[2]
            else:
                excinfo.exc_type = abc.AnyType()
                excinfo.var_name = None
                excbody = exc
            self.exceptions.append(excinfo)
            self.bytecodes.append(catchlabel)
            self.bytecodes.append(bytecode.getlocal_0())
            self.bytecodes.append(bytecode.pushscope())
            if hasattr(self, 'activation'):
                self.bytecodes.append(bytecode.getlocal(self.activation))
                self.bytecodes.append(bytecode.pushscope())
            self.bytecodes.append(bytecode.newcatch(excinfo))
            self.bytecodes.append(bytecode.pop())
            if variable is None:
                self.bytecodes.append(bytecode.pop())
            else:
                self.do_assign(variable)
            self.exec_suite(excbody)
            # TODO: kill variable
            self.bytecodes.append(bytecode.jump(endlabel))
        self.bytecodes.append(elselabel)
        if node.else_:
            self.exec_suite(node.else_)
        self.bytecodes.append(endlabel)

    def visit_return(self, node, void):
        assert void == True
        self.push_value(node.expr)
        self.bytecodes.append(bytecode.returnvalue())

    def visit_raise(self, node, void):
        assert void == True
        self.push_value(node.expr)
        self.bytecodes.append(bytecode.throw())

    def visit_break(self, node, void):
        assert void == True
        self.bytecodes.append(bytecode.jump(self.loopstack[-1][1]))

    def visit_continue(self, node, void):
        assert void == True
        self.bytecodes.append(bytecode.jump(self.loopstack[-1][0]))

    ##### Boolean operations #####

    def visit_not(self, node, void):
        if void:
            self.execute(node.expr)
        else:
            self.push_value(node.expr)
            self.bytecodes.append(bytecode.not_())

    def visit_or(self, node, void):
        endlabel = bytecode.Label()
        self.push_value(node.left)
        self.bytecodes.append(bytecode.dup())
        self.bytecodes.append(bytecode.iftrue(endlabel))
        self.bytecodes.append(bytecode.pop())
        self.push_value(node.right)
        self.bytecodes.append(endlabel)

    def visit_and(self, node, void):
        endlabel = bytecode.Label()
        self.push_value(node.left)
        self.bytecodes.append(bytecode.dup())
        self.bytecodes.append(bytecode.iffalse(endlabel))
        self.bytecodes.append(bytecode.pop())
        self.push_value(node.right)
        self.bytecodes.append(endlabel)

    ##### Math #####

    def visit_negate(self, node, void):
        if void:
            self.execute(node.expr)
        else:
            self.push_value(node.expr)
            self.bytecodes.append(bytecode.negate())

    @binary
    def visit_add(self, node):
        self.bytecodes.append(bytecode.add())

    @binary
    def visit_subtract(self, node):
        self.bytecodes.append(bytecode.subtract())

    @binary
    def visit_multiply(self, node):
        self.bytecodes.append(bytecode.multiply())

    @binary
    def visit_divide(self, node):
        self.bytecodes.append(bytecode.divide())

    @binary
    def visit_modulo(self, node):
        self.bytecodes.append(bytecode.modulo())

    ##### Comparison #####

    @binary
    def visit_equal(self, node):
        self.bytecodes.append(bytecode.strictequals())

    @binary
    def visit_notequal(self, node):
        self.bytecodes.append(bytecode.strictequals())
        self.bytecodes.append(bytecode.not_())

    @binary
    def visit_greater(self, node):
        self.bytecodes.append(bytecode.greaterthan())

    @binary
    def visit_greatereq(self, node):
        self.bytecodes.append(bytecode.greaterequals())

    @binary
    def visit_less(self, node):
        self.bytecodes.append(bytecode.lessthan())

    @binary
    def visit_lesseq(self, node):
        self.bytecodes.append(bytecode.lessequals())

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
        globals['String'] = Class(lib.get_class('', 'String'))
        globals['Number'] = Class(lib.get_class('', 'Number'))
        globals['Error'] = Class(lib.get_class('', 'Error'))
        globals['TypeError'] = Class(lib.get_class('', 'TypeError'))
        globals['ArgumentError'] = Class(lib.get_class('', 'ArgumentError'))
    code_header = CodeHeader(args[0])
    NameCheck(ast) # fills closure variable names
    frag = CodeFragment(ast, lib, code_header,
        private_namespace=args[0]+'$',
        filename=args[0],
        )
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
