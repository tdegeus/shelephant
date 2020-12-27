'''shelephant_rm
    Remove files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

Usage:
    shelephant_rm [options]
    shelephant_rm [options] <input.yaml>

Argument:
    YAML-file with filenames. Default: shelephant_dump.yaml

Options:
    -k, --key=N     Path in the YAML-file, separated by "/". [default: /]
    -f, --force     Remove without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os

from .. import __version__
from .. import YamlGetItem
from .. import PrefixPaths


def main():

    args = docopt.docopt(__doc__, version=__version__)
    key = list(filter(None, args['--key'].split('/')))
    source = args['<input.yaml>'] if args['<input.yaml>'] else 'shelephant_dump.yaml'
    files = YamlGetItem(source, key)
    prefix = os.path.dirname(source)
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
