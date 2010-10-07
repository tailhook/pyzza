from distutils.core import setup
from distutils.command.build_py import build_py as _build_py
import glob, sys, os.path

class build_py26(_build_py):

    def __init__(self, *args, **kwargs):
        _build_py.__init__(self, *args, **kwargs)
        from lib2to3 import refactor
        self.rtool = refactor.RefactoringTool(
            refactor.get_fixers_from_package('backport'))

    def find_package_modules(self, package, package_dir):
        res = _build_py.find_package_modules(self, package, package_dir)
        if package == 'pyzza':
            if sys.version_info < (2, 7):
                res.append((package, 'collections',
                    os.path.join(os.path.dirname(package_dir),
                        'backport', 'collections.py')))
            badio = ('pyzza', 'io', os.path.join('pyzza', 'io.py'))
            if badio in res:
                res.remove(badio)
                res.append(('pyzza', 'io', 'backport/io.py'))
        return res

    def copy_file(self, source, target, preserve_mode=True):
        if source.endswith('.py') and not 'backport' in source:
            with open(source, 'rt') as input:
                nval = self.rtool.refactor_string(input.read(), source)
            with open(target, 'wt') as output:
                output.write(
                    'from __future__ import print_function, absolute_import\n')
                output.write('from contextlib import nested\n')
                output.write(str(nval))
        else:
            _build_py.copy_file(self, source, target,
                preserve_mode=preserve_mode)

setup(
    name = "pyzza",
    version = "0.2.13",

    packages = ['pyzza'],
    scripts = [
        'scripts/pyzza-swf',
        'scripts/pyzza-cook',
        'scripts/pyzza-make',
        'scripts/pyzza-compile',
        ],
    package_dir = {'pyzza': 'pyzza'},
    package_data = {'pyzza': [
        'Grammar.txt',
        ]},
    data_files = [
        ('share/pyzza', glob.glob('lib/*.py')),
        ('share/pyzza/layout', glob.glob('lib/layout/*.py')),
        ],

    cmdclass={'build_py': build_py26} if sys.version_info[0] < 3 else {},

    # metadata for upload to PyPI
    author = "Paul Colomiets",
    author_email = "pc@gafol.net",
    description = 'Pyzza is a compiler of a python-like programming language, '
        'targeting the Flash platform',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        ],
    license = "MIT",
    keywords = "flash pyzza",
    url = "http://github.com/tailhook/pyzza",
    download_url = "http://github.com/tailhook/pyzza/downloads",
    requires = 'pyyaml',
)
