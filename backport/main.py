from lib2to3 import refactor
import os.path
import glob
import shutil

rtool = refactor.RefactoringTool(refactor.get_fixers_from_package('backport'))
for fn in glob.glob(os.path.join('pyzza', '*.py')):
    with open(fn, 'rt', encoding='utf-8') as f:
        val = f.read()
        nval = rtool.refactor_string(val, fn)
    with open(os.path.join('26', fn), 'wt', encoding='utf-8') as o:
        o.write('from __future__ import print_function, absolute_import\n')
        o.write('from contextlib import nested\n')
        o.write(str(nval))
oldio = os.path.join(os.path.dirname(__file__), 'io.py')
with open(oldio, 'rt', encoding='utf-8') as f:
    with open(os.path.join('26','pyzza','io.py'), 'wt', encoding='utf-8') as o:
        shutil.copyfileobj(f, o)
