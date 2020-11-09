'''yaml_dump
    Dump filenames to a new YAML-file.

Usage:
    yaml_dump [options] <file>...

Options:
    -o, --output=N      Output YAML-file. [default: dump.yaml]
    -p, --path=N        Path within the YAML-file separated by "/". [default: /]
    -c, --command       Interpret the input as a command.
    -f, --force         Force overwrite
    -n, --normpath      Normalize file-paths.
    -r, --relpath       Convert to a relative file-path
    -a, --abspath       Convert file-paths to absolute paths.
        --prefix=N      Add a prefix to all file-paths.
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/yaml_cli
'''

import docopt
import click
import os
import sys
import yaml
import operator
import functools
import subprocess

from .. import __version__


def Error(text):
    r'''
Command-line error: show message and quit with exit code "1"
    '''

    print(text)
    sys.exit(1)


def YamlDump(filename, data, force):
    r'''
Dump data to YAML file.
    '''

    if not force:
        if os.path.isfile(filename):
            if not click.confirm('Overwrite "{0:s}"?'.format(filename)):
                sys.exit(1)

    with open(filename, 'w') as file:
        ret = yaml.dump(data, file)


def main():
    r'''
Main program.
    '''

    args = docopt.docopt(__doc__, version=__version__)

    if args['--command']:
        command = ' '.join(args['<file>'])
        files = sorted(list(filter(None, subprocess.check_output(
            command, shell=True).decode('utf-8').split('\n'))))
    else:
        files = args['<file>']

    path = list(filter(None, args['--path'].split('/')))

    if len(path) > 0:
        data = functools.reduce(lambda x, y: {y: x}, path[:-1], {path[-1]: files})
    else:
        data = files

    if args['--normpath']:
        files = [os.path.normpath(file) for file in files]

    if args['--relpath']:
        files = [os.path.relpath(file) for file in files]

    if args['--abspath']:
        files = [os.path.abspath(file) for file in files]

    if args['--prefix']:
        files = [os.path.join(args['--prefix'], file) for file in files]

    YamlDump(args['--output'], data, args['--force'])

if __name__ == '__main__':

    main()
