'''shelephant_checksum
    Get checksum of files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

:usage:

    shelephant_checksum [options] <input.yaml>

:argument:

    YAML-file with file-paths. Default: shelephant_dump.yaml

:options:

    -o, --output=N
        Output YAML-file. [default: shelephant_checksum.yaml]

    -k, --key=N
        Path in the YAML-file, separated by "/". [default: /]

    -l, --local=N
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

from .. import version
from .. import YamlGetItem
from .. import YamlDump
from .. import PrefixPaths
from .. import GetChecksums


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
        files = YamlGetItem(source, key)
        prefix = os.path.dirname(source)
        files = PrefixPaths(prefix, files)
        data = GetChecksums(files, args.local, hybrid=True, progress=not args.quiet)
        YamlDump(args.output, data, args.force)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
