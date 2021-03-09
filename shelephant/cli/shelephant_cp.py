'''Copy files listed in a (field of a) YAML-file.
The filenames are assumed either absolute, or relative to the input YAML-file.

:usage:

    shelephant_cp [options] <destination>

    shelephant_cp [options] <input.yaml> <destination>

:arguments:

    <input.yaml>
        YAML-file with filenames. Default: shelephant_dump.yaml

    <destination>
        Prefix of the destination.

:options:

    -c, --checksum
        Use checksum to skip files that are the same.

    --check-rsync
        Check if files are different using *rsync*.
        *rsync* uses basic criteria such as file size and creation and modification date.
        This is much faster than using checksums but is only approximate.
        Note that *rsync* can also check based on checksum, enabled using ``--checksum``.

    --temp=arg
        Temporary filename to communicate with *rsync*. [default: shelephant_files.txt]

    -k, --key=arg
        Path in the YAML-file, separated by "/". [default: /]

    --colors=arg
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
import shutil
import os

from .. import version
from .. import detail
from .. import yaml


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-c', '--checksum', required=False, action='store_true')
        parser.add_argument('-r', '--check-rsync', required=False, action='store_true')
        parser.add_argument(      '--temp', required=False, default='shelephant_files.txt')
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

        return detail.copy(
            copy_function = shutil.copy2,
            files = yaml.read_item(source, key),
            src_dir = os.path.dirname(source),
            dest_dir = dest_dir,
            checksum = args.checksum,
            check_rsync = None if not args.check_rsync else args.temp,
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
