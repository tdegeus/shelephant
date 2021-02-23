'''shelephant_get
    Copy files using earlier collected information on which files to copy from where.
    By default the back-end is ``rysnc -a --from-file="temp" host:source_dir dest_dir``.
    Alternatively ``scp -p host:source_file dest_file`` can be used.
    Typically, ``rsync`` will be faster, especially in copying a lot of small files.

:usage:

    shelephant_get [options]

    shelephant_get [options] <hostinfo.yaml>

:argument:

    YAML-file with host information. Default: shelephant_hostinfo.yaml

:options:

    -l, --local=N
        Add local 'host' information to use precomputed checksums.

    --scp
        Use ``scp`` instead of ``rysnc`` as backend.

    --temp=N
        Temporary filename to communicate with rsync. [default: shelephant_files.txt]

    --colors=M
        Select color scheme from: none, dark. [default: dark]

    -s, --summary
        Print summary (and no details unless specified).

    -d, --details
        Print details (and no summary unless specified).

    -f, --force
        Force overwrite of all existing (but not matching) files.

    --verbose
        Verbose all commands.

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
import shutil

from .. import version
from .. import YamlRead
from .. import CopyFromRemote
from .. import RsyncFromRemote
from .. import ShelephantCopy
from .. import ShelephantCopySSH


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-l', '--local', required=False)
        parser.add_argument(      '--scp', required=False, action='store_true')
        parser.add_argument(      '--temp', required=False, default='shelephant_files.txt')
        parser.add_argument(      '--colors', required=False, default='dark')
        parser.add_argument('-s', '--summary', required=False, action='store_true')
        parser.add_argument('-d', '--details', required=False, action='store_true')
        parser.add_argument('-f', '--force', required=False, action='store_true')
        parser.add_argument(      '--verbose', required=False, action='store_true')
        parser.add_argument('-q', '--quiet', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('hostinfo', nargs='?', default='shelephant_hostinfo.yaml')
        args = parser.parse_args()

        source = args.hostinfo
        data = YamlRead(source)

        if 'host' not in data:

            ShelephantCopy(
                copy_function = shutil.copy2,
                files = data['files'],
                src_dir = data['prefix'],
                dest_dir = os.path.dirname(source),
                checksum = 'checksum' in data,
                quiet = args.quiet,
                force = args.force,
                print_details = not (args.force or args.summary) or args.details,
                print_summary = not (args.force or args.details) or args.summary,
                print_all = args.details,
                theme_name = args.colors.lower(),
                yaml_hostinfo_src = source,
                yaml_hostinfo_dest = args.local)

        elif args.scp:

            ShelephantCopySSH(
                copy_function = CopyFromRemote,
                host = data['host'],
                files = data['files'],
                src_dir = data['prefix'],
                dest_dir = os.path.dirname(source),
                checksum = 'checksum' in data,
                quiet = args.quiet,
                force = args.force,
                print_details = not (args.force or args.summary) or args.details,
                print_summary = not (args.force or args.details) or args.summary,
                print_all = args.details,
                verbose = args.verbose,
                theme_name = args.colors.lower(),
                yaml_hostinfo_src = source,
                yaml_hostinfo_dest = args.local)

        else:

            ShelephantCopySSH(
                copy_function = RsyncFromRemote,
                host = data['host'],
                files = data['files'],
                src_dir = data['prefix'],
                dest_dir = os.path.dirname(source),
                checksum = 'checksum' in data,
                quiet = args.quiet,
                force = args.force,
                print_details = not (args.force or args.summary) or args.details,
                print_summary = not (args.force or args.details) or args.summary,
                print_all = args.details,
                verbose = args.verbose,
                theme_name = args.colors.lower(),
                yaml_hostinfo_src = source,
                yaml_hostinfo_dest = args.local,
                tempfilename = args.temp)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
