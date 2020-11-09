'''yaml_rm
    Remove files listed in a (field of a) YAML-file.

Usage:
    yaml_rm [options] <input.yaml>

Options:
    -p, --path=N    Path within the YAML-file separated by "/". [default: /]
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/yaml_cli
'''

import docopt
import click
import os
import sys
import yaml
import operator
import functools

from .. import __version__


def Error(text):
    r'''
Command-line error: show message and quit with exit code "1"
    '''

    print(text)
    sys.exit(1)


def ReadYaml(filename):
    r'''
Read YAML file.
    '''

    if not os.path.isfile(filename):
        Error('"{0:s} does not exist'.format(filename))

    return yaml.load(open(filename, 'r').read(), Loader=yaml.FullLoader)


def main():
    r'''
Main program.
    '''

    args = docopt.docopt(__doc__, version=__version__)
    data = ReadYaml(args['<input.yaml>'])
    path = list(filter(None, args['--path'].split('/')))
    try:
        files = functools.reduce(operator.getitem, path, data)
    except:
        Error('"{0:s}" not in {1:s}'.format(args['--path'], args['<input.yaml>'])

    if len(files) == 0:
        sys.exis(0)

    for file in files:
        print('rm {0:s}'.format(file))

    if not click.confirm('Proceed?'):
        sys.exit(1)

    for file in files:
        os.remove(file)

if __name__ == '__main__':

    main()
