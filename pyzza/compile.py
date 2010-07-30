from itertools import chain, count, islice
from operator import methodcaller, attrgetter, itemgetter
from collections import defaultdict
from contextlib import contextmanager
import copy
import sys
import os.path

from . import parser, library, swf, bytecode, abc, tags

class SyntaxError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.context = kwargs

class NameError(SyntaxError): pass
class ImportError(SyntaxError): pass
class NotAClassError(SyntaxError): pass
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

    def add_method_body(self, name, frag, arguments=None):
        mi = abc.MethodInfo()
        mi.param_type = [abc.AnyType() for i in frag.arguments[1:]]
        mi.return_type = abc.AnyType()
        mi.name = name
        mi.flags = 0
        if arguments:
            options = []
            for a in arguments:
                if not hasattr(a, 'default'): continue
                if isinstance(a.default, parser.Number):
                    options.append(abc.OptionDetail(a.default.value))
                elif isinstance(a.default, parser.String):
                    options.append(abc.OptionDetail(a.default.value))
                elif isinstance(a.default, parser.Name):
                    options.append(abc.OptionDetail(
                        const_names[a.default.value]))
                else:
                    raise NotImplementedError(a.default)
            if options:
                mi.options = options
        if hasattr(frag, 'activation'):
            mi.flags |= abc.MethodInfo.NEED_ACTIVATION
        if frag.varargument:
            mi.flags |= abc.MethodInfo.NEED_REST
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
                    abc.QName(abc.NSPrivate(frag.filename), k),
                    abc.TraitSlot(v.index),
                    attr=0))
        mb.traits_info = traits
        mb.bytecode = frag.bytecodes
        self.tag.real_body.method_body_info.append(mb)
        return mb

    def add_class(self, name, bases, frag, package, slots=()):
        cls = abc.ClassInfo()
        inst = abc.InstanceInfo()
        cls.instance_info = inst
        cls.cinit = frag._method_info
        traits = []
        for (k, m) in frag.namespace.items():
            if k == '__init__': continue
            if isinstance(m, Property):
                traits.append(abc.TraitsInfo(
                    abc.QName(abc.NSPackage(''), k),
                    abc.TraitSlot(),
                    attr=0))
            elif isinstance(m, ClassMethod):
                trait = abc.TraitsInfo(
                    abc.QName(abc.NSPackage(''), k),
                    abc.TraitMethod(m.code_fragment._method_info),
                    attr=0)
                if m.code_fragment.metadata:
                    trait.metadata = [abc.MetadataInfo('pyzza')]
                    trait.metadata[0].item_info.update(m.code_fragment.metadata)
                traits.append(trait)
        cls.trait = traits
        inst.name = abc.QName(package, name)
        inst.super_name = bases[0].name
        inst.flags = 0
        inst.interface = []
        inst.iinit = frag.namespace['__init__'].code_fragment._method_info
        traits = []
        for (k, m) in frag.namespace.items():
            if k == '__init__': continue
            if isinstance(m, Method):
                flag = 0
                disp_id = 0
                fullname = abc.QName(m.namespace, k)
                for b in bases:
                    basetrait = b.get_method_trait(fullname)
                    if basetrait is not None:
                        flag = abc.TraitsInfo.ATTR_Override
                        disp_id = basetrait.disp_id
                        break
                trait = abc.TraitsInfo(
                    fullname,
                    abc.TraitMethod(m.code_fragment._method_info, disp_id),
                    attr=flag)
                if m.code_fragment.metadata:
                    trait.metadata = [abc.MetadataInfo('pyzza')]
                    trait.metadata[0].item_info.update(m.code_fragment.metadata)
                traits.append(trait)
        if slots:
            sealed = True
            for (index, k) in enumerate(slots):
                if k == '__dict__':
                    sealed = False
                    continue
                traits.append(abc.TraitsInfo(
                    abc.QName(abc.NSPackage(''), k),
                    abc.TraitSlot(),
                    attr=0))
            if sealed:
                inst.flags |= abc.InstanceInfo.CONSTANT_ClassSealed
        inst.trait = traits
        self.tag.real_body.class_info.append(cls)
        return cls

    def add_main_script(self, frag):
        script = abc.ScriptInfo()
        script.init = frag._method_info
        trait = []
        for (name, val) in frag.namespace.items():
            if isinstance(val, NewClass):
                trait.append(abc.TraitsInfo(val.class_info.name,
                    abc.TraitClass(0, val.class_info.class_info)))
            elif isinstance(val, NewFunction):
                trait.append(abc.TraitsInfo(val.property_name,
                    abc.TraitMethod(val.method_info)))
            elif isinstance(val, Property):
                trait.append(abc.TraitsInfo(val.property_name,
                    abc.TraitSlot()))
        script.traits_info = trait
        self.tag.real_body.script_info.append(script)
        return script

    def make_tag(self):
        return self.tag

##### Name types #####
class NameType:
    """Type of namespace bindings"""

class Property(NameType):
    """Property of a global namespace"""
    def __init__(self, name=None):
        self.name = name

    @property
    def property_name(self):
        return self.name

    def __repr__(self):
        return '<{0} {1!r}>'.format(self.__class__.__name__, self.property_name)

class LocalProperty(Property):
    """Property of a local namespace (for eval mode)"""

class Class(Property):
    """Imported class"""
    def __init__(self, cls):
        super().__init__(cls.name)
        self.class_info = cls

class NewClass(Property):
    """In-source class"""

class NewFunction(Property):
    """In-source class"""

class Register(NameType):
    """Register reference, can have register number or can have no number"""
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return '<R{0:d}>'.format(self.value)
        else:
            return '<R:{0:x}>'.format(id(self))

class ClsRegister(Register):
    """Special register that means ``self`` for classmethod"""

class Builtin(NameType):
    """Some built-in (for global namespace)"""

class ClosureSlot(NameType):
    """Closure variable"""
    def __init__(self, idx, name):
        self.index = idx
        self.name = name

class Method(NameType):
    """Method (for class namespace)"""
    def __init__(self, frag, namespace=abc.NSPackage('')):
        self.code_fragment = frag
        self.namespace = namespace

class ClassMethod(NameType):
    """Class method (for class namespace)"""
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

const_names = {
    'True': True,
    'False': False,
    'None': None,
    'undefined': abc.Undefined(),
}
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
    'min': Builtin('min'),
    'max': Builtin('max'),
    'len': Builtin('len'),
    'isinstance': Builtin('isinstance'),
    }

class Globals:
    namespace = globals
    def __init__(self):
        self.namespace = self.namespace.copy()
    def update(self, val):
        self.namespace.update(val)

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
        parser.ImportStmt: 'import',
        }

    def __init__(self, node):
        self.allnames = set()
        self.imported = set()
        self.exports = set()
        self.public = set()
        if hasattr(node, 'arguments'):
            self.localnames = set(map(attrgetter('name.value'), node.arguments))
        else:
            self.localnames = set()
        self.functions = []
        for n in (node.body if hasattr(node, 'body') else node):
            assert n is not None, node
            self.visit(n)
        self.annotate(node)

    def annotate(self, node):
        exvars = set(self.exports)
        glob = set()
        for f in self.functions:
            exvars.update(f.func_globals & self.localnames)
            glob.update(f.func_globals - self.localnames)
        node.func_export = frozenset(exvars)
        node.func_locals = frozenset(self.localnames)
        node.func_globals = frozenset(glob | self.allnames - self.localnames)
        node.func_imports = frozenset(self.imported)
        node.func_publicnames = frozenset(self.public)
        if hasattr(self, 'slots'):
            assert isinstance(node, parser.Class)
            node.class_slots = self.slots
        #~ print(getattr(node, 'name', None),
            #~ node.func_globals, node.func_locals, node.func_export)

    def visit_function(self, node):
        NameCheck(node)
        if node.decorators:
            for i in node.decorators:
                if i.name.value == 'package':
                    self.public.add((i.arguments[0].value, node.name.value,
                        'function'))
        self.localnames.add(node.name.value)
        self.functions.append(node)

    def visit_class(self, node):
        NameCheck(node)
        if node.decorators:
            for i in node.decorators:
                if i.name.value == 'package':
                    self.public.add((i.arguments[0].value, node.name.value,
                    'class'))
        self.localnames.add(node.name.value)
        self.exports.add(node.name.value)
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
            if node.target.value == '__slots__':
                assert isinstance(node.expr, (parser.Tuple, parser.ListMaker)), node.expr
                assert all(isinstance(n, parser.String) for n in node.expr)
                self.slots = tuple(map(attrgetter('value'), node.expr))
            self.localnames.add(node.target.value)
        elif isinstance(node.target, parser.Tuple):
            for n in node.target:
                if isinstance(n, parser.Name):
                    self.localnames.add(n.value)
        for n in node:
            self.visit(n)

    def visit_import(self, node):
        for name in node.names:
            if isinstance(name, parser.Name):
                self.imported.add(name.value)
            elif isinstance(name, parser.Assoc):
                self.imported.add(name.alias.value)
            else:
                raise NotImplementedError(name)

    def visit_for(self, node):
        for v in node.var:
            if isinstance(v, parser.Name):
                self.localnames.add(v.value)
            elif isinstance(v, parser.Tuple):
                for n in v:
                    if isinstance(n, parser.Name):
                        self.localnames.add(n.value)
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
        parser.Del: 'delete',
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
        parser.Ternary: 'inlineif',
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
    statement_nodes = (
        parser.ImportStmt, parser.Class, parser.Func, parser.Assign,
        parser.Del, parser.Return, parser.Raise, parser.If, parser.For,
        parser.While, parser.Try, parser.Break, parser.Continue,
        )
    max_stack = None
    local_count = None
    scope_stack_init = 0 # TODO: fix
    scope_stack_max = 10 # TODO: fix
    def __init__(self, ast, library, code_header,
            parent_namespaces,
            mode="global", #class_body, method, function, eval, evalchildfunc
            arguments=(None,),
            varargument=None,
            filename=None,
            classmethod=False,
            metadata={},
            myclass=None,
            ):
        self.library = library
        self.code_header = code_header
        self.bytecodes = [
            bytecode.debugfile(filename),
            bytecode.debugline(getattr(ast, 'lineno', 0)),
            bytecode.getlocal_0(),
            bytecode.pushscope(),
            ]
        if mode == 'class_body':
            self.class_name = ast.name
            assert not ast.func_export
            self.namespace = {k: Property(abc.QName(abc.NSPackage(''),k))
                for k in ast.func_locals}
        elif mode == 'eval':
            self.bytecodes.append(bytecode.getlocal_0())
            self.bytecodes.append(bytecode.pushwith())
            self.namespace = {k: LocalProperty(abc.QName(abc.NSPackage(''),k))
                for k in ast.func_locals}
        else:
            self.namespace = {k: Register() for k in ast.func_locals
                if k not in ast.func_export}
        for k in ast.func_imports:
            self.namespace[k] = Property()
        if ast.func_export:
            if mode == 'global':
                self.namespace.update((k, Property(
                    abc.QName(abc.NSPrivate(filename), k)))
                    for (idx, k) in enumerate(ast.func_export))
            elif mode in ('method', 'function', 'evalchildfunc'):
                self.activation = Register()
                self.bytecodes.append(bytecode.newactivation())
                self.bytecodes.append(bytecode.dup())
                self.bytecodes.append(bytecode.pushscope())
                self.bytecodes.append(bytecode.setlocal(self.activation))
                self.namespace.update((k, ClosureSlot(idx+1, k))
                    for (idx, k) in enumerate(ast.func_export))
            elif mode == 'eval':
                pass
                # no registers anyway
            else:
                raise NotImplementedError(mode)

        self.loopstack = [] # pairs of continue label and break label
        # extra registers used for computations
        # keyed by register type
        self.method_name = getattr(ast, 'name', self.qname('__global__'))
        self.myclass = myclass
        self.classmethod = classmethod
        self.extra_registers = defaultdict(list)
        self.exceptions = []
        self.mode = mode
        self.parent_namespaces = parent_namespaces
        self.arguments = arguments
        self.varargument = varargument
        self.filename = filename
        self.current_line = None
        self.metadata = metadata
        for (i, v) in enumerate(chain(arguments, (varargument,))):
            if mode == 'eval' and v is not None:
                self.bytecodes.append(bytecode.getlocal_0())
                self.bytecodes.append(bytecode.getlocal(Register(i)))
                self.bytecodes.append(bytecode.setproperty(self.qname(v)))
            elif v in ast.func_export:
                self.bytecodes.append(bytecode.getlocal(
                    self.activation))
                self.bytecodes.append(bytecode.getlocal(Register(i)))
                self.bytecodes.append(bytecode.setslot(
                    self.namespace[v].index))
            else:
                self.namespace[v] = Register(i)
        if self.classmethod:
            self.namespace[arguments[0]] = ClsRegister(0)
        for args in ast.func_publicnames:
            self.library.add_name(*args)
        self.exec_suite(ast.body if hasattr(ast, 'body') else ast,
            eval=mode == 'eval')
        self.bytecodes.append(bytecode.returnvoid())
        self.fix_registers()
        self.verify_stack()

    ##### Post-processing #####

    def fix_registers(self):
        rcount = defaultdict(int)
        for bcode in self.bytecodes:
            for (name, typ, _, _) in bcode.format:
                if issubclass(typ, bytecode.Register):
                    r = getattr(bcode, name)
                    if r.value is None:
                        rcount[r] += 1
        regs = {}
        argnum = len(self.arguments)
        if self.varargument:
            argnum += 1
        for (idx, (name, freq)) in zip(count(argnum),
            sorted(rcount.items(), key=itemgetter(1))):
            regs[name] = idx
        self.local_count = argnum + len(regs)
        for bcode in self.bytecodes:
            for (name, typ, _, _) in bcode.format:
                if issubclass(typ, bytecode.Register):
                    rname = getattr(bcode, name)
                    if rname.value is None:
                        rval = regs[rname]
                    else:
                        rval = rname.value
                    setattr(bcode, name, bytecode.Register(rval))
        bcodes = []
        for (k, v) in self.namespace.items():
            if isinstance(v, Register) and v in regs:
                bcodes.append(bytecode.debug(1, k, regs[v], 0))
        self.bytecodes[2:2] = bcodes

    def verify_stack(self):
        stack_size = 0
        max_stack_size = 0
        for bcode in self.bytecodes:
            if stack_size < len(bcode.stack_before):
                raise StackError("Not enought operands in the stack for "
                    "{0!r} (operands: {1})".format(bcode, bcode.stack_before))
            if isinstance(bcode, bytecode.Label):
                if hasattr(bcode, '_verify_stack'):
                    if bcode._verify_stack != stack_size:
                        raise StackError("Unbalanced stack at {0!r}".format(bcode))
                else:
                    bcode._verify_stack = stack_size
            old_stack = stack_size
            stack_size += len(bcode.stack_after) - len(bcode.stack_before)
            if isinstance(bcode, bytecode.JumpBytecode):
                if hasattr(bcode.offset, '_verify_stack'):
                    if bcode.offset._verify_stack != stack_size:
                        raise StackError("Unbalanced stack at {0!r}".format(bcode))
                else:
                    bcode.offset._verify_stack = stack_size
            #~ print('[{0:3d} -{1:2d}] {2}'.format(old_stack, stack_size, bcode))
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

    def exec_suite(self, suite, eval=False):
        if eval:
            if not isinstance(suite[-1], self.statement_nodes):
                val = suite[-1]
                suite = suite[:-1]
                context = ('', (val.lineno, val.col))
                suite.append(parser.Return([
                    parser.Leaf("return", context),
                    val], context))
        for line in suite:
            self.execute(line)

    def find_name(self, name, node):
        for ns in chain((self,), self.parent_namespaces):
            if name in ns.namespace:
                break
        else:
            if self.mode == 'eval':
                self.namespace[name] = LocalProperty(self.qname(name))
                ns = self
            elif self.mode == 'evalchildfunc':
                self.namespace[name] = Property(self.qname(name))
                ns = self
            else:
                raise NameError(name, filename=self.filename,
                    lineno=node.lineno, column=node.col)
        return ns.namespace[name]

    def qname(self, name):
        return abc.QName(abc.NSPackage(''), name)

    def qpriv(self, name):
        return abc.QName(abc.NSPrivate(self.filename), name)

    def get_extra_reg(self, type):
        try:
            return self.extra_registers[type].pop()
        except IndexError:
            return Register()

    def free_extra_reg(self, reg, type):
        self.bytecodes.append(bytecode.kill(reg))
        self.extra_registers[type].append(reg)

    @contextmanager
    def extra_reg(self, type):
        reg = self.get_extra_reg(type)
        try:
            yield reg
        finally:
            self.free_extra_reg(reg, type)

    ##### Visitors #####

    def visit_import(self, node, void):
        assert void == True
        for name in node.names:
            package = node.module.value
            if isinstance(name, parser.Name):
                name = name.value
                alias = name
            elif isinstance(name, parser.Assoc):
                alias = name.alias.value
                name = name.name.value
            else:
                raise NotImplementedError(name)
            prop = self.namespace[alias]
            assert isinstance(prop, Property)
            try:
                typ = self.library.get_property_type(package, name)
                if typ == 'class':
                    cls = self.library.get_class(package, name)
                    prop.__class__ = Class
                    prop.class_info = cls
                    prop.name = cls.name
                elif typ == 'function':
                    prop.name = abc.QName(abc.NSPackage(package), name)
                else:
                    raise NotImplementedError(typ)
            except library.PropertyNotFoundError:
                raise ImportError('{0}:{1}'.format(package, name),
                    filename=self.filename, lineno=node.lineno, column=node.col)

    def visit_class(self, node, void):
        assert void == True
        package = abc.NSPrivate(self.filename)
        if node.decorators:
            for i in node.decorators:
                if i.name.value == 'package':
                    package = abc.NSPackage(i.arguments[0].value)
                elif i.name.value == 'private':
                    package = abc.NSPrivate(self.filename)
                else:
                    raise NotImplementedError("No decorator ``{0}''"
                        .format(i.name))
        frag = CodeFragment(node, self.library, self.code_header,
            mode="class_body",
            parent_namespaces=(self,) + self.parent_namespaces,
            filename=self.filename,
            )
        self.code_header.add_method_body(node.name.value, frag)
        assert len(node.bases) <= 1
        if not node.bases:
            val = self.library.get_class('', 'Object')
        else:
            name = self.find_name(node.bases[0].value, node.bases[0])
            try:
                val = name.class_info
            except AttributeError:
                raise NotAClassError(
                    "Imported name {!r} not found or not a class"
                    .format(name.property_name), filename=self.filename,
                    lineno=node.bases[0].lineno, column=node.bases[0].col)
        bases = []
        while val:
            bases.append(val)
            val = val.get_base()
        cls = self.code_header.add_class(node.name.value, bases, frag,
            package=package, slots=getattr(node, 'class_slots', ()))
        prop = self.namespace[node.name.value]
        if isinstance(prop, Property):
            prop.__class__ = NewClass
            prop.name = abc.QName(package, prop.name.name)
            prop.code = frag
            prop.class_info = self.library.add_class(cls)
        with self.assign(node.name):
            for i in reversed(bases):
                self.bytecodes.append(bytecode.getlex(i.name))
                self.bytecodes.append(bytecode.pushscope())
            self.bytecodes.append(bytecode.getlex(bases[0].name))
            self.bytecodes.append(bytecode.newclass(cls))
            for i in range(len(bases)):
                self.bytecodes.append(bytecode.popscope())

    def visit_function(self, node, void):
        assert void == True
        args = node.arguments
        if len(args) >= 1 and isinstance(args[-1], parser.Vararg):
            vararg = args[-1].name.value
            args = args[:-1]
        else:
            vararg = None
        if self.mode == 'class_body':
            classmethod = False
            staticmethod = False
            metadata = {}
            methodns = abc.NSPackage('')
            if node.decorators:
                for i in node.decorators:
                    if i.name.value == 'classmethod':
                        classmethod = True
                    elif i.name.value == 'staticmethod':
                        staticmethod = True
                    elif i.name.value == 'debuglevel':
                        metadata['debuglevel'] = i.arguments[0].value
                    elif i.name.value == 'debuginfo':
                        metadata['debuginfo'] = ','.join(arg.value
                            for arg in i.arguments)
                    elif i.name.value == 'nsuser':
                        methodns = abc.NSUser(i.arguments[0].value)
                    else:
                        raise NotImplementedError("No decorator ``{0}''"
                            .format(i.name))
            frag = CodeFragment(node, self.library, self.code_header,
                mode="method",
                parent_namespaces=self.parent_namespaces,
                arguments=([None] if staticmethod else []) +
                    list(map(attrgetter('name.value'), args)),
                varargument=vararg,
                filename=self.filename,
                classmethod=classmethod,
                metadata=metadata,
                myclass=self,
                )
            if classmethod or staticmethod:
                self.namespace[node.name.value] = ClassMethod(frag)
            else:
                self.namespace[node.name.value] = Method(frag, methodns)
            self.code_header.add_method_body(
                '{0}/{1}'.format(self.class_name.value, node.name.value),
                frag, node.arguments)
        else:
            package = abc.NSPrivate(self.filename)
            method = False
            mode = "function"
            if 'eval' in self.mode:
                mode = "evalchildfunc"
            if node.decorators:
                for i in node.decorators:
                    if i.name.value == 'package':
                        package = abc.NSPackage(i.arguments[0].value)
                    elif i.name.value == 'private':
                        package = abc.NSPrivate(self.filename)
                    elif i.name.value == 'method':
                        method = True
                    elif i.name.value == '__eval__':
                        mode = 'eval'
                    else:
                        raise NotImplementedError("No decorator ``{0}''"
                            .format(i.name))
            frag = CodeFragment(node, self.library, self.code_header,
                mode=mode,
                parent_namespaces=(self,) + self.parent_namespaces,
                arguments=([] if method else [None]) + list(
                    map(attrgetter('name.value'), args)),
                varargument=vararg,
                filename=self.filename,
                )
            mbody = self.code_header.add_method_body(
                '{0}${1:d}:{2}'.format(self.filename,
                node.lineno, node.name.value),
                frag, node.arguments)
            prop = self.namespace[node.name.value]
            if isinstance(prop, Property) and len(self.parent_namespaces) <= 1:
                prop.__class__ = NewFunction
                prop.code = frag
                prop.method_info = mbody.method
                prop.name = abc.QName(package, prop.name.name)
                # don't need to assign global functions
                # they are like methods on global object
            else:
                with self.assign(node.name):
                    self.bytecodes.append(bytecode.newfunction(mbody.method))

    @contextmanager
    def assign(self, target, _swap=False):
        if isinstance(target, parser.Name):
            reg = self.namespace[target.value]
            if isinstance(reg, ClosureSlot):
                self.bytecodes.append(bytecode.getlocal(self.activation))
                if _swap:
                    self.bytecodes.append(bytecode.swap())
            elif isinstance(reg, LocalProperty):
                extra = self.get_extra_reg('*')
                startlabel = bytecode.Label()
                endtrylabel = bytecode.Label()
                endcatchlabel = bytecode.Label()
                excinfo = abc.ExceptionInfo()
                excinfo.exc_from = startlabel
                excinfo.exc_to = endtrylabel
                excinfo.target = endtrylabel
                excinfo.exc_type = self.qname("ReferenceError")
                excinfo.var_name = None
                self.exceptions.append(excinfo)
                self.bytecodes.append(startlabel)
                self.bytecodes.append(bytecode.findpropstrict(reg.name))
                self.bytecodes.append(bytecode.coerce_a())
                self.bytecodes.append(bytecode.setlocal(extra))
                self.bytecodes.append(bytecode.jump(endcatchlabel))
                self.bytecodes.append(endtrylabel)
                self.bytecodes.append(bytecode.getlocal_0())
                self.bytecodes.append(bytecode.pushscope())
                self.bytecodes.append(bytecode.getlocal_0())
                self.bytecodes.append(bytecode.pushwith())
                self.bytecodes.append(bytecode.newcatch(excinfo))
                self.bytecodes.append(bytecode.pop()) # some info
                self.bytecodes.append(bytecode.pop()) # exception var
                self.bytecodes.append(bytecode.getlocal_0())
                self.bytecodes.append(bytecode.coerce_a())
                self.bytecodes.append(bytecode.setlocal(extra))
                self.bytecodes.append(endcatchlabel)
                self.bytecodes.append(bytecode.getlocal(extra))
            elif isinstance(reg, Property):
                self.bytecodes.append(bytecode.getscopeobject(0))
        elif isinstance(target, parser.GetAttr):
            self.push_value(target.expr)
            if _swap:
                self.bytecodes.append(bytecode.swap())
        elif isinstance(target, parser.Subscr):
            self.push_value(target.expr)
            self.push_value(target.index)
            if _swap:
                raise NotImplementedError(target)
        elif isinstance(target, parser.Tuple):
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
                elif isinstance(reg, LocalProperty):
                    self.bytecodes.append(bytecode.setproperty(
                        reg.property_name))
                    self.free_extra_reg(extra, '*')
                elif isinstance(reg, Property):
                    self.bytecodes.append(bytecode.initproperty(
                        reg.property_name))
                else:
                    raise NotImplementedError(reg)
            elif isinstance(target, parser.GetAttr):
                self.bytecodes.append(bytecode.setproperty(
                    self.qname(target.name.value)))
            elif isinstance(target, parser.Subscr):
                self.bytecodes.append(bytecode.setproperty(
                    abc.MultinameL(abc.NamespaceSetInfo(abc.NSPackage('')))))
            elif isinstance(target, parser.Tuple):
                for (idx, node) in enumerate(target):
                    if idx < len(target)-1:
                        self.bytecodes.append(bytecode.dup())
                    self.bytecodes.append(bytecode.pushbyte(idx))
                    self.bytecodes.append(bytecode.getproperty(
                       abc.MultinameL(abc.NamespaceSetInfo(abc.NSPackage('')))))
                    self.do_assign(node)
            else:
                raise NotImplementedError(target)

    def do_assign(self, target):
        with self.assign(target, _swap=True):
            pass

    def visit_assign(self, node, void):
        assert void == True
        if self.mode == 'class_body' and isinstance(node.target, parser.Name)\
            and node.target.value == '__slots__':
            return
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

    def visit_delete(self, node, void):
        assert void == True
        self._delete(node.expr)

    def _delete(self, node):
        if isinstance(node, parser.Name):
            reg = self.namespace[node.value]
            if isinstance(reg, ClosureSlot):
                self.bytecodes.append(bytecode.getlocal(self.activation))
                self.bytecodes.append(bytecode.pushundefined())
                self.bytecodes.append(bytecode.setslot(reg.index))
            elif isinstance(reg, Property):
                self.bytecodes.append(bytecode.getscopeobject(0))
                self.bytecodes.append(bytecode.deleteproperty(
                    reg.property_name))
                self.bytecodes.append(bytecode.pop())
            elif isinstance(reg, Register):
                self.bytecodes.append(bytecode.kill(reg))
            else:
                raise NotImplementedError(reg)
        elif isinstance(node, parser.GetAttr):
            self.push_value(node.expr)
            self.bytecodes.append(bytecode.deleteproperty(
                self.qname(node.name.value)))
            self.bytecodes.append(bytecode.pop())
        elif isinstance(node, parser.Subscr):
            self.push_value(node.expr)
            self.push_value(node.index)
            self.bytecodes.append(bytecode.deleteproperty(
                abc.MultinameL(abc.NamespaceSetInfo(abc.NSPackage('')))))
            self.bytecodes.append(bytecode.pop())
        elif isinstance(node, parser.Tuple):
            for n in node:
                self._delete(n)
        else:
            raise NotImplementedError(node)

    def visit_call(self, node, void):
        name = node.expr
        if isinstance(name, parser.Name):
            name = name.value
            val = self.find_name(name, node.expr)
            if isinstance(val, (Class, NewClass)):
                self.bytecodes.append(bytecode.getlex(val.property_name))
                for i in node.arguments:
                    self.push_value(i)
                self.bytecodes.append(bytecode.construct(
                    len(node.arguments)))
                if void:
                    self.bytecodes.append(bytecode.pop())
            elif isinstance(val, ClsRegister):
                self.bytecodes.append(bytecode.getlocal(val))
                for i in node.arguments:
                    self.push_value(i)
                self.bytecodes.append(bytecode.construct(
                    len(node.arguments)))
                if void:
                    self.bytecodes.append(bytecode.pop())
            elif isinstance(val, Builtin):
                getattr(self, 'call_' + val.name)(node, void)
            else:
                self.push_value(node.expr)
                self.bytecodes.append(bytecode.pushnull())
                for i in node.arguments:
                    self.push_value(i)
                self.bytecodes.append(bytecode.call(len(node.arguments)))
                if void:
                    self.bytecodes.append(bytecode.pop())
        else:
            if isinstance(name, parser.Call) and name.expr.value == 'Class'\
                and len(name.arguments) == 1:
                self.push_value(name.arguments[0])
                self.bytecodes.append(bytecode.coerce(
                    abc.QName(abc.NSPackage(''), 'Class')))
                for i in node.arguments:
                    self.push_value(i)
                self.bytecodes.append(bytecode.construct(len(node.arguments)))
                if void:
                    self.bytecodes.append(bytecode.pop())
                return
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
            if self.mode == 'eval':
                self.namespace[name] = LocalProperty(self.qname(name))
                ns = self
            elif self.mode == 'evalchildfunc':
                self.namespace[name] = Property(self.qname(name))
                ns = self
            else:
                raise NameError(name, filename=self.filename,
                    lineno=node.lineno, column=node.col)
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
                self.bytecodes.append(bytecode.getlex(self.qpriv(val.name)))
        elif isinstance(val, Property):
            if val.name in self.namespace:
                self.bytecodes.append(bytecode.getscopeobject(0))
                self.bytecodes.append(bytecode.getproperty(val.property_name))
            else:
                self.bytecodes.append(bytecode.getlex(val.property_name))
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
            if node.value < 128:
                self.bytecodes.append(bytecode.pushbyte(node.value))
            elif node.value < 65536:
                self.bytecodes.append(bytecode.pushshort(node.value))
            else:
                self.bytecodes.append(bytecode.pushint(node.value))
        else:
            raise NotImplementedError(node)

    def _get_meta(self, node):
        if isinstance(node.expr, parser.Name):
            obj = self.find_name(node.expr.value, node.expr)
            if isinstance(obj, (Class, NewClass)):
                qname = self.qname(node.attribute.value)
                trait = obj.class_info.get_method_trait(qname, raw_trait=True)
                if hasattr(trait, 'metadata'):
                    for m in trait.metadata:
                        if m.name != 'pyzza': continue
                        return m

    def visit_callattr(self, node, void):
        meta = self._get_meta(node)
        if meta and 'debuglevel' in meta.item_info and False: # TOFIX
            if not void:
                self.bytecodes.append(bytecode.pushint())
            return
        self.push_value(node.expr)
        nargs = len(node.arguments)
        if meta and 'debuginfo' in meta.item_info:
            loginfo = meta.item_info['debuginfo'].split(',')
            for name in loginfo:
                if name == 'line':
                    self.bytecodes.append(bytecode.pushint(node.lineno))
                    nargs += 1
                elif name == 'file':
                    self.bytecodes.append(bytecode.pushstring(self.filename))
                    nargs += 1
                elif name == 'class':
                    self.bytecodes.append(bytecode.pushstring(
                        self.myclass.class_name.value
                        if self.myclass else ''))
                    nargs += 1
                elif name == 'method':
                    self.bytecodes.append(bytecode.pushstring(
                        self.method_name.value))
                    nargs += 1
                else:
                    raise ValueError(name)
        for i in node.arguments:
            self.push_value(i)
        if void:
            self.bytecodes.append(bytecode.callpropvoid(
                self.qname(node.attribute.value),
                nargs))
        else:
            self.bytecodes.append(bytecode.callproperty(
                self.qname(node.attribute.value),
                nargs))

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

    def visit_inlineif(self, node, void):
        endlabel = bytecode.Label()
        self.push_value(node.cond)
        lab = bytecode.Label()
        self.bytecodes.append(bytecode.iffalse(lab))
        self.execute(node.expr1, void)
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(bytecode.jump(endlabel))
        self.bytecodes.append(bytecode.pop())
        self.bytecodes.append(lab)
        self.execute(node.expr2, void)
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(endlabel)

    def visit_for(self, node, void):
        assert void == True
        if isinstance(node.expr, parser.Call) \
            and isinstance(node.expr.expr, parser.Name):
            val = self.find_name(node.expr.expr.value, node.expr.expr)
            if isinstance(val, Builtin):
                getattr(self, 'loop_' + val.name)(node)
            else:
                raise NotImplementedError(node.expr.expr)
        else:
            raise NotImplementedError(node.expr)

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
                excinfo.exc_type = self.find_name(exc[0].value,
                    exc[0]).class_info.name
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
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(bytecode.dup())
        self.bytecodes.append(bytecode.iftrue(endlabel))
        self.bytecodes.append(bytecode.pop())
        self.push_value(node.right)
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(endlabel)
        if void:
            self.bytecodes.append(bytecode.pop())

    def visit_and(self, node, void):
        endlabel = bytecode.Label()
        self.push_value(node.left)
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(bytecode.dup())
        self.bytecodes.append(bytecode.iffalse(endlabel))
        self.bytecodes.append(bytecode.pop())
        self.push_value(node.right)
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(endlabel)
        if void:
            self.bytecodes.append(bytecode.pop())

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

    ##### Built-in functions #####

    def call_abs(self, node, void):
        assert len(node.arguments) == 1
        endlabel = bytecode.Label()
        self.push_value(node.arguments[0])
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(bytecode.dup())
        self.bytecodes.append(bytecode.pushbyte(0))
        self.bytecodes.append(bytecode.ifge(endlabel))
        self.bytecodes.append(bytecode.negate())
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(endlabel)

    def call_min(self, node, void):
        assert len(node.arguments) == 2
        endlabel = bytecode.Label()
        self.push_value(node.arguments[0])
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(bytecode.dup())
        with self.extra_reg('*') as reg:
            self.push_value(node.arguments[1])
            self.bytecodes.append(bytecode.dup())
            self.bytecodes.append(bytecode.coerce_a())
            self.bytecodes.append(bytecode.setlocal(reg))
            self.bytecodes.append(bytecode.ifle(endlabel))
            self.bytecodes.append(bytecode.pop())
            self.bytecodes.append(bytecode.getlocal(reg))
        self.bytecodes.append(endlabel)

    def call_max(self, node, void):
        assert len(node.arguments) == 2
        endlabel = bytecode.Label()
        self.push_value(node.arguments[0])
        self.bytecodes.append(bytecode.coerce_a())
        self.bytecodes.append(bytecode.dup())
        with self.extra_reg('*') as reg:
            self.push_value(node.arguments[1])
            self.bytecodes.append(bytecode.dup())
            self.bytecodes.append(bytecode.coerce_a())
            self.bytecodes.append(bytecode.setlocal(reg))
            self.bytecodes.append(bytecode.ifge(endlabel))
            self.bytecodes.append(bytecode.pop())
            self.bytecodes.append(bytecode.getlocal(reg))
        self.bytecodes.append(endlabel)

    def call_isinstance(self, node, void):
        # The following commented out code leads to segfault
        # at least on flashplayer 9.0.115.0 for linux
        # ... sorry
        #~ if isinstance(node.arguments[1], parser.Name):
            #~ name = self.find_name(node.arguments[1].value)
            #~ if isinstance(name, (Class, NewClass)):
                #~ self.push_value(node.arguments[0])
                #~ print(name.name)
                #~ self.bytecodes.append(bytecode.istype(name.name))
                #~ return
        self.push_value(node.arguments[0])
        self.push_value(node.arguments[1])
        self.bytecodes.append(bytecode.istypelate())

    ##### Built-in iterators #####

    def loop_objectiter(self, node, fun):
        endlabel = bytecode.Label()
        elselabel = bytecode.Label()
        assert len(node.expr.arguments) == 1, node.expr
        with self.extra_reg('*') as obj, \
             self.extra_reg('int') as idx:
            contlabel = bytecode.Label()
            bodylabel = bytecode.label()
            self.push_value(node.expr.arguments[0])
            self.bytecodes.append(bytecode.coerce_a())
            self.bytecodes.append(bytecode.setlocal(obj))
            self.bytecodes.append(bytecode.pushbyte(0))
            self.bytecodes.append(bytecode.setlocal(idx))
            self.bytecodes.append(bytecode.jump(contlabel))
            self.bytecodes.append(bodylabel)
            if fun == 'keys':
                var = node.var[0] if len(node.var) == 1 else node.var
                with self.assign(var):
                    self.bytecodes.append(bytecode.getlocal(obj))
                    self.bytecodes.append(bytecode.getlocal(idx))
                    self.bytecodes.append(bytecode.nextname())
            elif fun == 'values':
                var = node.var[0] if len(node.var) == 1 else node.var
                with self.assign(var):
                    self.bytecodes.append(bytecode.getlocal(obj))
                    self.bytecodes.append(bytecode.getlocal(idx))
                    self.bytecodes.append(bytecode.nextvalue())
            elif fun == 'items':
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
            self.bytecodes.append(elselabel)
            if node.else_:
                self.exec_suite(node.else_)
            self.bytecodes.append(endlabel)

    def loop_keys(self, node, **kw):
        self.loop_objectiter(node, 'keys', **kw)

    def loop_values(self, node, **kw):
        self.loop_objectiter(node, 'values', **kw)

    def loop_items(self, node, **kw):
        self.loop_objectiter(node, 'items', **kw)

    def loop_range(self, node):
        endlabel = bytecode.Label()
        elselabel = bytecode.Label()
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
        with self.extra_reg('int') as stepreg, \
             self.extra_reg('int') as iterreg, \
             self.extra_reg('int') as stopreg:
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
            if step == 1:
                self.bytecodes.append(bytecode.inclocal_i(iterreg))
            else:
                self.bytecodes.append(bytecode.getlocal(iterreg))
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
            self.bytecodes.append(elselabel)
            if node.else_:
                self.exec_suite(node.else_)
            self.bytecodes.append(endlabel)

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
    op.add_option('-m', '--main-class', metavar="CLASS",
        help="Use CLASS as class for root movie clip (default Main)",
        dest="main_class", default='Main', type="string")
    op.add_option('-o', '--output', metavar="SWFFILE",
        help="Output swf data into SWFFILE.",
        dest="output", default=None, type="string")
    op.add_option('-w', '--width', metavar="PIXELS",
        help="Width of output flash movie in pixels",
        dest="width", default=600, type="int")
    op.add_option('-t', '--height', metavar="PIXELS",
        help="Height of output flash movie in pixels",
        dest="height", default=600, type="int")
    op.add_option('-f', '--frame-rate', metavar="FPS",
        help="Frame rate of output flash movie",
        dest="frame_rate", default=15, type="int")
    op.add_option('--debug-filename', metavar="MODE",
        help="How to put filename into debugging info. `full` - full path, "
             " `basename` - filename without path",
        dest="debug_filenames", default="full", type="choice",
        choices=("full", "basename"))
    return op

def print_error(e):
    print("{error.__class__.__name__} at line {lineno} column {column} "\
        "of file {filename!r}:".format(error=e, **e.context))
    try:
        with open(e.context['filename'], 'rt', encoding='utf-8') as f:
            for (no, line) in islice(zip(count(1), f),
                max(e.context['lineno']-5, 0), e.context['lineno']+4):
                print('{0:4d}  {1}'.format(no, line.rstrip()))
                if no == e.context['lineno']:
                    print(' ' * (e.context['column']+6) + '^')
    except IOError:
        pass
    print("{0.__class__.__name__}: {0.message}".format(e))

def make_globals(lib, std_globals=True):
    glob = Globals()
    for pack, name in lib.get_public_names():
        if pack == '':
            try:
                glob.namespace[name] = Class(lib.get_class(pack, name))
            except library.ClassNotFoundError:
                prop = Property(abc.QName(abc.NSPackage(''), name))
                glob.namespace[name] = prop
    if std_globals:
        glob.namespace['str'] = Class(lib.get_class('', 'String'))
        glob.namespace['float'] = Class(lib.get_class('', 'Number'))
        glob.namespace['list'] = Class(lib.get_class('', 'Array'))
        glob.namespace['bool'] = Class(lib.get_class('', 'Boolean'))
    return glob

def compile(files, lib, glob, output, main_class,
        width=500, height=375, frame_rate=15, filenames='full'):
    code_tags = []
    for file in files:
        if hasattr(file, 'read'):
            ast = parser.parser().parse_stream(file, name=file.name)
            fname = file.name
        else:
            ast = parser.parser().parse_file(file)
            fname = file
        code_header = CodeHeader(fname)
        NameCheck(ast) # fills closure variable names
        if filenames == 'basename':
            fname = os.path.basename(fname)
        else:
            fname = fname
        frag = CodeFragment(ast, lib, code_header, filename=fname,
            parent_namespaces=(glob,))
        code_header.add_method_body('', frag)
        code_header.add_main_script(frag)
        code_tags.append(code_header.make_tag())
    h = swf.Header(frame_size=(int(width*20), int(height*20)),
                   frame_rate=int(frame_rate*256))
    content = [tags.FileAttributes()] \
        + code_tags + [
        tags.SymbolClass(main_class=main_class),
        tags.ShowFrame(),
        ]
    if hasattr(output, 'write'):
        h.write_swf(output, b''.join(map(methodcaller('blob'), content)))
    else:
        with open(output, 'wb') as o:
            h.write_swf(o, b''.join(map(methodcaller('blob'), content)))

def main():
    global options
    op = get_options()
    options, args = op.parse_args()
    if len(args) < 1:
        op.error("At least one argument expected")
    from . import parser, library
    lib = library.Library()
    for i in options.libraries:
        lib.add_file(i)
    if options.output:
        out = options.output
    else:
        if args[0] == '-':
            out = sys.stdout.buffer
        elif args[0].endswith('.py'):
            out = args[0][:-3] + '.swf'
        else:
            out = args[0] + '.swf'
    for i, val in enumerate(args):
        if val == '-':
            args[i] = sys.stdin.buffer
    glob = make_globals(lib, std_globals=options.std_globals)
    try:
        compile(args, lib, glob, out, main_class=options.main_class,
            width=options.width, height=options.height,
            frame_rate=options.frame_rate, filenames=options.debug_filenames)
    except (parser.SyntaxError, SyntaxError) as e:
        print_error(e)
        return

if __name__ == '__main__':
    from . import compile
    compile.main()
