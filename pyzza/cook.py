import os.path
import warnings
from collections import deque, defaultdict

import yaml

from . import parser, library, compile

class Visitor(object):
    visitors = {
        parser.Func: 'function',
        parser.Class: 'class',
        parser.ImportStmt: 'import',
        }

    def __init__(self, node):
        self.imports = set()
        self.exports = set()
        for n in (node.body if hasattr(node, 'body') else node):
            assert n is not None, node
            self.visit(n)

    def visit_function(self, node):
        vis = Visitor(node)
        if node.decorators:
            for i in node.decorators:
                if i.name.value == 'package':
                    self.exports.add((i.arguments[0].value, node.name.value))
        self.imports.update(vis.imports)

    def visit_class(self, node):
        vis = Visitor(node)
        if node.decorators:
            for i in node.decorators:
                if i.name.value == 'package':
                    self.exports.add((i.arguments[0].value, node.name.value))
        self.imports.update(vis.imports)


    def visit_import(self, node):
        for name in node.names:
            if isinstance(name, parser.Name):
                self.imports.add((node.module.value, name.value))
            elif isinstance(name, parser.Assoc):
                self.imports.add((node.module.value, name.name.value))
            else:
                raise NotImplementedError(name)

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

def visit(ast):
    v = Visitor(ast)
    return v.imports, v.exports

def get_options():
    import optparse
    op = optparse.OptionParser("%prog [-f cookfile] [-o dir] [-vqFDn]")
    op.add_option('-f', '--filename', metavar="COOKFILE",
        help="File that contains build specifications",
        dest="filename", default='Cookfile', type="string")
    op.add_option('-o', '--output-dir', metavar='DIR',
        help="Dir to place output files",
        dest="build_dir", default='.', type="string")
    op.add_option('-v', '--verbose',
        help="Print more info",
        dest="verbosity", default=0, action="count")
    op.add_option('-q', '--quiet',
        help="Print less info",
        dest="quietness", default=0, action="count")
    op.add_option('-F', '--force-rebuild',
        help="Rebuild all (even if nothing changed)",
        dest="force_rebuild", default=False, action="store_true")
    op.add_option('-D', '--no-cache',
        help="Do not cache dependencies into COOKFILE.dep file"
             " (will scan all files each run)",
        dest="cache", default=True, action="store_false")
    op.add_option('-n', '--dry-run',
        help="Do not build anything just scan dependencies and print commands"
             "to be executed",
        dest="dry_run", default=False, action="store_true")
    return op

def gather_dependencies(recipe):
    return update_dependencies({}, recipe)

def _makedeps(fullname):
    ext = os.path.splitext(fullname)[1]
    if ext == '.py':
        try:
            ast = parser.parser().parse_file(fullname)
        except parser.SyntaxError as e:
            try:
                if options.verbosity > 1:
                    from .compile import print_error
                    print_error(e)
            except (NameError, ImportError):
                raise
            warnings.warn("Syntax error in file {!r}".format(fullname))
            return
        except Exception:
            warnings.warn("File {!r} can't be parsed".format(fullname))
            raise
            return
        imports, exports = visit(ast)
        return {
            'time': os.path.getmtime(fullname),
            'exports': list(exports),
            'imports': list(imports),
            }
    elif ext in ('.swf', '.swc'):
        ex = list(library.get_public_names(fullname))
        return {
            'time': os.path.getmtime(fullname),
            'exports': ex,
            }
    else:
        raise NotImplementedError(ext)

def update_dependencies(dependencies, recipe):
    def adddeps(info):
        for i in info.get('exports', ()):
            if i in exists:
                warnings.warn("Class {0[0]}:{0[1]} is contained in "
                              "both {1!r} and {2!r}"
                              .format(i, fullname, exists[i]))
            else:
                exists[i] = fullname
                if i in needed:
                    for val in needed[i]:
                        val['depends'].add(fullname)
                    del needed[i]
        deps = set(info.get('depends', ()))
        for i in info.get('imports', ()):
            if i in exists:
                deps.add(exists[i])
            else:
                needed[i].append(info)
        info['depends'] = deps
    exists = {}
    needed = defaultdict(list)
    for fullname, info in dependencies.items():
        if os.path.getmtime(fullname) != info['time']:
            info = _makedeps(fullname)
            if not info:
                continue
            dependencies[fullname] = info
        adddeps(info)
    for name, info in recipe['Targets'].items():
        if 'main-source' in info:
            fullname = os.path.realpath(
                os.path.join(recipe['_dir'], info['main-source']))
            if fullname not in dependencies:
                info = _makedeps(fullname)
                if not info:
                    continue
                dependencies[fullname] = info
                adddeps(info)
    if needed:
        for libname in recipe['Global'].get('libraries', ()):
            fullname = os.path.realpath(os.path.join(recipe['_dir'], libname))
            if fullname in dependencies:
                continue
            info = _makedeps(fullname)
            if not info:
                continue
            dependencies[fullname] = info
            adddeps(info)
            if not needed:
                break
    if needed:
        for dir in recipe['Global'].get('pyzza-path', ()):
            for root, dirs, files in os.walk(os.path.join(recipe['_dir'], dir)):
                dirs[:] = [i for i in dirs if not i.startswith('.')]
                for f in files:
                    if os.path.splitext(f)[1] != '.py':
                        continue
                    fullname = os.path.realpath(os.path.join(root, f))
                    if fullname in dependencies:
                        continue
                    info = _makedeps(fullname)
                    if not info:
                        continue
                    dependencies[fullname] = info
                    adddeps(info)
                    if not needed:
                        break
    if needed:
        for name in needed:
            warnings.warn("Name `{0}:{1}' not found".format(*name))
    # Removing unneeded dependencies using Mark and Sweep :) algorithm
    queue = deque()
    alldeps = set()
    for name, info in recipe['Targets'].items():
        if 'main-source' in info:
            queue.append(os.path.realpath(
                os.path.join(recipe['_dir'], info['main-source'])))
    while queue:
        file = queue.popleft()
        alldeps.add(file)
        for k in dependencies[file].get('depends', ()):
            if k not in alldeps:
                queue.append(k)
    return {k:v for k, v in dependencies.items() if k in alldeps}


def build(files, output, recipe, info):
    lib = library.Library()
    for fname in recipe['Global'].get('libraries', ()):
        lib.add_file(fname)
    filename_mode = recipe['Global'].get('debug-filename', 'full')
    compile.compile((f for f in files if f.endswith('.py')),
        lib, compile.make_globals(lib), output,
        width=info.get('width', 500), height=info.get('height', 375),
        frame_rate=info.get('frame-rate', 15),
        main_class=info.get('main-class', 'Main'),
        filenames=filename_mode)

def files(src, dependencies):
    all = [src]
    for fname in all:
        for dname in dependencies[fname].get('depends', ()):
            if fname in dependencies[dname].get('depends', ()):
                warnings.warn("Circular dependency between {0!r} and {1!r}"
                    .format(fname, dname))
            else:
                all.append(dname)
    res = []
    visited = set()
    for v in reversed(all):
        if v not in visited:
            res.append(v)
            visited.add(v)
    return list(reversed(res))

def make(recipe, dependencies, force=False, verbosity=0):
    for name, info in recipe['Targets'].items():
        if 'main-source' in info:
            src = os.path.realpath(os.path.join(
                recipe['_dir'], info['main-source']))
            targ = os.path.join(recipe['_builddir'], name)
            need_build = force or not os.path.exists(targ)
            filelist = list(reversed(list(files(src, dependencies))))
            if not need_build:
                targtime = os.path.getmtime(targ)
                for f in filelist:
                    if dependencies[f]['time'] > targtime:
                        need_build = True
                        break
            if need_build:
                if verbosity > 1:
                    print("File {0!r} will be build from the following sources:"
                        .format(targ))
                    for f in filelist:
                        print("    {0}".format(f))
                build(filelist, targ, recipe, info)
            elif verbosity > 1:
                print("File {0!r} is skipped".format(targ))
        else:
            raise NotImplementedError('Please specify source file for {0!r}'
                .format(name))

def main():
    global options
    op = get_options()
    options, args = op.parse_args()
    if args:
        op.error("No arguments expected")
    options.verbosity -= options.quietness
    with open(options.filename) as file:
        recipe = yaml.load(file)
        recipe['_dir'] = os.path.dirname(os.path.abspath(options.filename))
        recipe['_builddir'] = os.path.realpath(options.build_dir)
    if os.path.exists(options.filename + '.dep') and options.cache:
        with open(options.filename + '.dep', 'rt') as depfile:
            dependencies = yaml.load(depfile)
        dependencies = update_dependencies(dependencies, recipe)
    else:
        dependencies = gather_dependencies(recipe)
    if options.cache:
       with open(options.filename + '.dep', 'wt') as depfile:
           yaml.dump(dependencies, depfile)
    make(recipe, dependencies, force=options.force_rebuild,
        verbosity=options.verbosity)

if __name__ == '__main__':
    main()
