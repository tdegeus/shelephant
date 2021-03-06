'''Get checksum of files listed in a (field of a) YAML-file.
The filenames are assumed either absolute, or relative to the input YAML-file.

:usage:

    shelephant_checksum [options] <input.yaml>

:argument:

    YAML-file with file-paths. Default: shelephant_dump.yaml

:options:

    -o, --output=arg
        Output YAML-file. [default: shelephant_checksum.yaml]

    -k, --key=arg
        Path in the YAML-file, separated by "/". [default: /]

    -l, --local=arg
        Add local 'host' information to use precomputed checksums.

    -f, --force
        Overwrite output file without prompt.

    -q, --quiet
        Do not print progress.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import argparse
import os

from .. import checksum
from .. import relpath
from .. import version
from .. import yaml


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-o', '--output', required=False, default='shelephant_checksum.yaml')
        parser.add_argument('-k', '--key', required=False, default='/')
        parser.add_argument('-l', '--local', required=False)
        parser.add_argument('-f', '--force', required=False, action='store_true')
        parser.add_argument('-q', '--quiet', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('input', nargs='?', default='shelephant_dump.yaml')
        args = parser.parse_args()

        source = args.input
        key = list(filter(None, args.key.split('/')))
        files = yaml.read_item(source, key)
        prefix = os.path.dirname(source)
        files = relpath.add_prefix(prefix, files)
        data = checksum.get(files, args.local, hybrid=True, progress=not args.quiet)
        yaml.dump(args.output, data, args.force)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
