'''shelephant_rm
    Remove files listed in a (field of a) YAML-file.
    By default the filenames are assumed either absolute, or relative to the working directory.
    Using another prefix by:
    --dir       Reading it from the same YAML-file.
    --prefix    Specifying it as command-line option.

Usage:
    shelephant_rm [options] <input.yaml>

Options:
    -p, --path=N    Path where files are stored in the YAML-file, separated by "/". [default: /]
        --dir=N     Path where prefix-directory is stored in the YAML-file, separated by "/".
        --prefix=N  Prefix directory.
    -f, --force     Remove without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
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
    prefix = None

    if args['--dir']:
        prefix = GetList(args['<input.yaml>'], args['--dir'])
    elif args['--prefix']:
        prefix = args['--prefix']

    if prefix:
        files = [os.path.join(prefix, file) for file in files]

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
