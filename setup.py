from distutils.core import setup
import glob

setup(
    name = "pyzza",
    version = "0.1",

    packages = ['pyzza'],
    scripts = [
        'scripts/pyzza-swf',
        'scripts/pyzza-cook',
        'scripts/pyzza-make',
        'scripts/pyzza-compile',
        ],
    package_dir = {'pyzza': 'pyzza'},
    package_data = {'pyzza': [
        'Grammar*',
        ]},
    data_files = [
        ('share/pyzza', glob.glob('lib/*.py')),
        ('share/pyzza/layout', glob.glob('lib/layout/*.py')),
        ],

    # metadata for upload to PyPI
    author = "Paul Colomiets",
    author_email = "pc@gafol.net",
    description = 'Pyzza is a compiler of a python-like programming language'
        'targeting Flash platform',
    license = "MIT",
    keywords = "flash pyzza",
    url = "http://www.mr-pc.kiev.ua/en/projects/Pyzza",
    requires = 'pyyaml',
)
