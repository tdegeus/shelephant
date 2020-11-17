'''shelephant_dump
    Dump filenames to a new YAML-file.

Usage:
    shelephant_dump [options] <file>...

Options:
    -o, --output=N      Output YAML-file. [default: shelephant_dump.yaml]
    -f, --force         Force overwrite of output file.
    -c, --command       Interpret the input as a command (instead of filenames).
    -a, --abspath       Store absolute paths (default: relative to the output file).
    -s, --sort          Sort filenames.
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
from . import YamlDump


def main():

    args = docopt.docopt(__doc__, version=__version__)
    prefix = os.path.dirname(args['--output'])

    if args['--command']:
        command = ' '.join(args['<file>'])
        files = sorted(list(filter(None, subprocess.check_output(
            command, shell=True).decode('utf-8').split('\n'))))
    else:
        files = args['<file>']

    if args['--abspath']:
        files = [os.path.abspath(file) for file in files]
    else:
        files = [os.path.relpath(file, prefix) for file in files]

    if args['--sort']:
        files = sorted(files)

    YamlDump(args['--output'], files, args['--force'])


if __name__ == '__main__':

    main()
