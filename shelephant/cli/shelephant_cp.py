'''shelephant_cp
    Copy files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

Usage:
    shelephant_cp [options] <destination>
    shelephant_cp [options] <input.yaml> <destination>

Argument:
    <input.yaml>    YAML-file with filenames. Default: shelephant_dump.yaml
    <destination>   Prefix of the destination.

Options:
    -c, --checksum  Use checksum to skip files that are the same.
    -k, --key=N     Path in the YAML-file, separated by "/". [default: /]
        --colors=M  Select color scheme from: none, dark. [default: dark]
    -q, --quiet     Do not print progress.
    -s, --summary   Print summary (and no details unless specified).
    -d, --details   Print details (and no summary unless specified).
    -f, --force     Move without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import shutil
import os

from .. import __version__
from .. import ShelephantCopy
from .. import YamlGetItem


def main():

    args = docopt.docopt(__doc__, version=__version__)

    source = args['<input.yaml>'] if args['<input.yaml>'] else 'shelephant_dump.yaml'
    key = list(filter(None, args['--key'].split('/')))

    return ShelephantCopy(
        copy_function = shutil.copy,
        files = YamlGetItem(source, key),
        src_dir = os.path.dirname(source),
        dest_dir = args['<destination>'],
        checksum = args['--checksum'],
        quiet = args['--quiet'],
        force = args['--force'],
        print_details = not (args['--force'] or args['--summary']) or args['--details'],
        print_summary = not (args['--force'] or args['--details']) or args['--summary'],
        print_all = args['--details'],
        theme_name = args['--colors'].lower())


if __name__ == '__main__':

    main()
