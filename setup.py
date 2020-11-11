
from setuptools import setup
from setuptools import find_packages

import re

filepath = 'shelephant/__init__.py'
__version__ = re.findall(r'__version__ = \'(.*)\'', open(filepath).read())[0]

setup(
    name = 'shelephant',
    version = __version__,
    license = 'MIT',
    author = 'Tom de Geus',
    author_email = 'tom@geus.me',
    description = 'YAML based shell commands',
    long_description = 'YAML based shell commands',
    keywords = 'YAML, Bash',
    url = 'https://github.com/tdegeus/shelephant',
    packages = find_packages(),
    install_requires = ['docopt>=0.6.2', 'click>=4.0', 'pyyaml>=1.0'],
    entry_points = {
        'console_scripts': [
            'shelephant_dump = shelephant.cli.shelephant_dump:main',
            'shelephant_get = shelephant.cli.shelephant_get:main',
            'shelephant_hash = shelephant.cli.shelephant_hash:main',
            'shelephant_hostinfo = shelephant.cli.shelephant_hostinfo:main',
            'shelephant_rm = shelephant.cli.shelephant_rm:main',
        ]})
