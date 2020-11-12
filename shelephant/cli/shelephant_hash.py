'''shelephant_hash
    Get hash of files listed in a (field of a) YAML-file.

    By default the filenames are assumed either absolute, or relative to the input YAML-file.
    To use another prefix:
    - Read the prefix from the input YAML-file (--dir).
    - Specify the prefix it as command-line option (--prefix).

Usage:
    shelephant_hash [options] <input.yaml>

Options:
    -o, --output=N  Output YAML-file. [default: selephant_hash.yaml]
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
from . import GetList
from . import YamlDump
from . import GetSHA256


def main():

    args = docopt.docopt(__doc__, version=__version__)
    path = list(filter(None, args['--path'].split('/')))
    files = GetList(args['<input.yaml>'], path)
    prefix = os.path.dirname(args['<input.yaml>'])

    if args['--dir']:
        prefix = GetString(args['<input.yaml>'], args['--dir'])
    elif args['--prefix']:
        prefix = args['--prefix']

    if not all([os.path.isabs(file) for file in files]):
        files = [os.path.normpath(os.path.join(prefix, file)) for file in files]

    data = [GetSHA256(file) for file in files]

    YamlDump(args['--output'], data, args['--force'])


if __name__ == '__main__':

    main()
