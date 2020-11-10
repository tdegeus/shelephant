'''yaml_rm
    Remove files listed in a (field of a) YAML-file.

Usage:
    yaml_rm [options] <input.yaml>

Options:
    -p, --path=N    Path within the YAML-file separated by "/". [default: /]
    -f, --force     Remove without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/yaml_cli
'''

import docopt
import click
import os
import sys

from .. import __version__
from . import Error
from . import GetList


def main():

    args = docopt.docopt(__doc__, version=__version__)
    path = list(filter(None, args['--path'].split('/')))
    files = GetList(args['<input.yaml>'], path)

    if len(files) == 0:
        sys.exis(0)

    for file in files:
        print('rm {0:s}'.format(file))

    if not args['--force']:
        if not click.confirm('Proceed?'):
            sys.exit(1)

    for file in files:
        os.remove(file)


if __name__ == '__main__':

    main()
