
from setuptools import setup
from setuptools import find_packages

import os
import re
import subprocess

git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode('UTF-8')
git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip().decode('UTF-8')

cmd = '''def git():
    return ("{0:s}", "{1:s}")
'''.format(git_branch, git_hash)

os.rename('shelephant/git.py', 'shelephant/git.py.bak')

with open('shelephant/git.py', 'w') as f:
    f.write(cmd)

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
    install_requires = ['docopt', 'click', 'pyyaml', 'mergedeep', 'numpy', 'tqdm'],
    entry_points = {
        'console_scripts': [
            'shelephant_checksum = shelephant.cli.shelephant_checksum:main',
            'shelephant_dump = shelephant.cli.shelephant_dump:main',
            'shelephant_extract = shelephant.cli.shelephant_extract:main',
            'shelephant_get = shelephant.cli.shelephant_get:main',
            'shelephant_merge = shelephant.cli.shelephant_merge:main',
            'shelephant_parse = shelephant.cli.shelephant_parse:main',
            'shelephant_hostinfo = shelephant.cli.shelephant_hostinfo:main',
            'shelephant_cp = shelephant.cli.shelephant_cp:main',
            'shelephant_mv = shelephant.cli.shelephant_mv:main',
            'shelephant_rm = shelephant.cli.shelephant_rm:main',
            'shelephant_send = shelephant.cli.shelephant_send:main',
        ]})

os.rename('shelephant/git.py.bak', 'shelephant/git.py')
