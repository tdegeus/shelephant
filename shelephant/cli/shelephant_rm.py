'''shelephant_rm
    Remove files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

Usage:
    shelephant_rm [options] <input.yaml>

Options:
    -p, --path=N    Path where files are stored in the YAML-file, separated by "/". [default: /]
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
from . import GetList
from . import GetString
from . import Error
from . import PrefixPaths


def main():

    args = docopt.docopt(__doc__, version=__version__)
    path = list(filter(None, args['--path'].split('/')))
    files = GetList(args['<input.yaml>'], path)
    prefix = os.path.dirname(args['<input.yaml>'])
    files = PrefixPaths(prefix, files)

    if len(files) == 0:
        return 0

    for file in files:
        print('rm {0:s}'.format(file))

    if not args['--force']:
        if not click.confirm('Proceed?'):
            return 1

    for file in files:
        os.remove(file)


if __name__ == '__main__':

    main()
