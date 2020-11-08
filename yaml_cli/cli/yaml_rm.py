'''yaml_rm
    Remove files listed in a YAML-file.

Usage:
    yaml_rm [options] <input>

Options:
    -p, --path=N    Path separated by "/". [default: /]
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/yaml_cli
'''

import docopt
import click
import os
import sys
import yaml

from .. import __version__


def error(text):
    r'''
Command-line error: show message and quit with exit code "1"
    '''

    print(text)
    sys.exit(1)


def read_yaml(filename):
    r'''
Read YAML file.
    '''

    if not os.path.isfile(filename):
        error('"{0:s} does not exist'.format(filename))

    return yaml.load(open(filename, 'r').read(), Loader=yaml.FullLoader)


def main():
    r'''
Main program.
    '''

    args = docopt.docopt(__doc__, version=__version__)

    data = read_yaml(args['<input>'])

    path = args['--path'].split('/')

    files = data[path[1]]

    for file in files:
        print('rm {0:s}'.format(file))

    if not click.confirm('Proceed?'):
        sys.exit(1)

    for file in files:
        os.remove(file)

if __name__ == '__main__':

    main()
