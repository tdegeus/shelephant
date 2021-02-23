'''shelephant_mv
    Move files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

:usage:

    shelephant_mv [options] <destination>

    shelephant_mv [options] <input.yaml> <destination>

:argument:

    <input.yaml>
        YAML-file with filenames. Default: shelephant_dump.yaml

    <destination>
        Prefix of the destination.

:options:

    -c, --checksum
        Use checksum to skip files that are the same.

    -k, --key=N
        Path in the YAML-file, separated by "/". [default: /]

    --colors=M
        Select color scheme from: none, dark. [default: dark]

    -s, --summary
        Print summary (and no details unless specified).

    -d, --details
        Print details (and no summary unless specified).

    -f, --force
        Move without prompt.

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
from .. import ShelephantCopy
from .. import YamlGetItem


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-c', '--checksum', required=False, action='store_true')
        parser.add_argument('-k', '--key', required=False, default='/')
        parser.add_argument(      '--colors', required=False, default='dark')
        parser.add_argument('-s', '--summary', required=False, action='store_true')
        parser.add_argument('-d', '--details', required=False, action='store_true')
        parser.add_argument('-f', '--force', required=False, action='store_true')
        parser.add_argument('-q', '--quiet', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('args', nargs='+')
        args = parser.parse_args()

        if len(args.args) == 1:
            source = 'shelephant_dump.yaml'
            dest_dir = args.args[0]
        elif len(args.args) == 2:
            source = args.args[0]
            dest_dir = args.args[1]
        else:
            raise IOError('Too many arguments specified')

        key = list(filter(None, args.key.split('/')))

        return ShelephantCopy(
            copy_function = os.rename,
            files = YamlGetItem(source, key),
            src_dir = os.path.dirname(source),
            dest_dir = dest_dir,
            checksum = args.checksum,
            quiet = args.quiet,
            force = args.force,
            print_details = not (args.force or args.summary) or args.details,
            print_summary = not (args.force or args.details) or args.summary,
            print_all = args.details,
            theme_name = args.colors.lower())

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
