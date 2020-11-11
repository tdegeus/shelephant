'''shelephant_dump
    Dump filenames to a new YAML-file.

Output file (dumppaths.yaml):

    working_diectory:
        /path/to/where/this/command/was/run
    files:
        - foo.txt
        - bar.txt

Usage:
    shelephant_dump [options] <file>...

Options:
    -o, --output=N      Output YAML-file. [default: dump.yaml]
    -c, --command       Interpret the input as a command.
    -f, --force         Force overwrite.
    -a, --abspath       Store absolute paths (default: relative to working directory).
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os
import sys
import functools
import subprocess

from .. import __version__
from . import Error
from . import YamlDump


def main():

    args = docopt.docopt(__doc__, version=__version__)

    data = {'working_diectory': os.getcwd()}

    if args['--command']:
        command = ' '.join(args['<file>'])
        data['files'] = sorted(list(filter(None, subprocess.check_output(
            command, shell=True).decode('utf-8').split('\n'))))
    else:
        data['files'] = args['<file>']

    if args['--abspath']:
        data['files'] = [os.path.abspath(file) for file in data['files']]
    else:
        data['files'] = [os.path.relpath(file) for file in data['files']]

    YamlDump(args['--output'], data, args['--force'])


if __name__ == '__main__':

    main()
