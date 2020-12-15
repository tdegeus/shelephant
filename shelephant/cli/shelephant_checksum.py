'''shelephant_checksum
    Get checksum of files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

Usage:
    shelephant_checksum [options]
    shelephant_checksum [options] <input.yaml>

Arguments:
    YAML-file with file-paths. Default: shelephant_dump.yaml

Options:
    -o, --output=N  Output YAML-file. [default: shelephant_checksum.yaml]
    -k, --key=N     Path in the YAML-file, separated by "/". [default: /]
    -f, --force     Overwrite output file without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import os

from .. import __version__
from . import YamlGetItem
from . import YamlDump
from . import PrefixPaths
from . import GetSHA256


def main():

    args = docopt.docopt(__doc__, version=__version__)
    source = args['<input.yaml>'] if args['<input.yaml>'] else 'shelephant_dump.yaml'
    key = list(filter(None, args['--key'].split('/')))
    files = YamlGetItem(source, key)
    prefix = os.path.dirname(source)
    files = PrefixPaths(prefix, files)
    data = [GetSHA256(file) for file in files]
    YamlDump(args['--output'], data, args['--force'])


if __name__ == '__main__':

    main()
