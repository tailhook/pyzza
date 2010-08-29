#!/usr/bin/env python3
# Old module, currently setup.py should do the work for you

from lib2to3 import refactor
import os.path
import glob
import shutil

if os.path.exists('26'):
    shutil.rmtree('26')
os.makedirs('26/pyzza')
rtool = refactor.RefactoringTool(refactor.get_fixers_from_package('backport'))
for fn in glob.glob(os.path.join('pyzza', '*.py')):
    with open(fn, 'rt', encoding='utf-8') as f:
        val = f.read()
        nval = rtool.refactor_string(val, fn)
    with open(os.path.join('26', fn), 'wt', encoding='utf-8') as o:
        o.write('from __future__ import print_function, absolute_import\n')
        o.write('from contextlib import nested\n')
        o.write(str(nval))
origdir = os.path.dirname(os.path.dirname(__file__))
shutil.copy(os.path.join(origdir,'backport','io.py'),
    os.path.join(origdir, '26','pyzza','io.py'))
shutil.copy(os.path.join(origdir,'backport','collections.py'),
    os.path.join(origdir, '26','pyzza','collections.py'))
shutil.copy(os.path.join(origdir,'setup.py'),
    os.path.join(origdir, '26'))
shutil.copy(os.path.join(origdir,'pyzza', 'Grammar.txt'),
    os.path.join(origdir, '26', 'pyzza'))
shutil.copytree(os.path.join(origdir, 'scripts'),
    os.path.join(origdir, '26', 'scripts'))
