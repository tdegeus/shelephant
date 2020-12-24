'''shelephant_mv
    Move files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

Usage:
    shelephant_mv [options] <destination>
    shelephant_mv [options] <input.yaml> <destination>

Argument:
    <input.yaml>    YAML-file with filenames. Default: shelephant_dump.yaml
    <destination>   Prefix of the destination.

Options:
    -c, --checksum  Use checksum to skip files that are the same.
    -k, --key=N     Path in the YAML-file, separated by "/". [default: /]
        --colors=M  Select color scheme from: none, dark. [default: dark]
    -q, --quiet     Do not print progress.
    -f, --force     Move without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os
import math

from .. import __version__
from . import ShelephantCopy


def main():

    args = docopt.docopt(__doc__, version=__version__)

    ShelephantCopy(
        operation = 'move',
        source = args['<input.yaml>'] if args['<input.yaml>'] else 'shelephant_dump.yaml',
        key = list(filter(None, args['--key'].split('/'))),
        dest_dir = args['<destination>'],
        theme_name = args['--colors'].lower(),
        checksum = args['--checksum'],
        quiet = args['--quiet'],
        force = args['--force'])


if __name__ == '__main__':

    main()
