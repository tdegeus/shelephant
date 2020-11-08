
from setuptools import setup
from setuptools import find_packages

import re

filepath = 'yaml_cli/__init__.py'
__version__ = re.findall(r'__version__ = \'(.*)\'', open(filepath).read())[0]

setup(
    name = 'yaml_cli',
    version = __version__,
    license = 'MIT',
    author = 'Tom de Geus',
    author_email = 'tom@geus.me',
    description = 'YAML based shell commands',
    long_description = 'YAML based shell commands',
    keywords = 'YAML, Bash',
    url = 'https://github.com/tdegeus/yaml_cli',
    packages = find_packages(),
    install_requires = ['docopt>=0.6.2', 'click>=4.0', 'pyyaml>=1.0'],
    entry_points = {
        'console_scripts': ['yaml_rm = yaml_cli.cli.yaml_rm:main']})
