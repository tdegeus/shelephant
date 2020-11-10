'''yaml_hash
    Get hash of files listed in a (field of a) YAML-file.

Usage:
    yaml_hash [options] <input.yaml>

Options:
    -o, --output=N      Output YAML-file. [default: hash.yaml]
    -p, --path=N        Path within the YAML-file separated by "/". [default: /]
    -f, --force         Remove without prompt.
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/yaml_cli
'''

import docopt
import click
import os
import sys

from .. import __version__
from . import Error
from . import GetList
from . import YamlDump
from . import GetSHA256


def main():

    args = docopt.docopt(__doc__, version=__version__)
    path = list(filter(None, args['--path'].split('/')))
    files = GetList(args['<input.yaml>'], path)
    data = [GetSHA256(file) for file in files]
    YamlDump(args['--output'], data, args['--force'])


if __name__ == '__main__':

    main()
