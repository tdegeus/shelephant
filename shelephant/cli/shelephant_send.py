'''shelephant_send
    Copy files to a remote, using earlier collected information on which files to copy where.
    By default the back-end is ``rysnc -a --from-file="temp" source_dir host:dest_dir``.
    Alternatively ``scp -p source_file host:dest_file`` can be used.
    Typically, ``rsync`` will be faster, especially in copying a lot of small files.

:usage:

    shelephant_send [options]

    shelephant_send [options] <files.yaml> <hostinfo.yaml>

:arguments:

    <files.yaml>
        YAML-file with files to send. Default: shelephant_dump.yaml

    <hostinfo.yaml>
        YAML-file with host information. Default: shelephant_hostinfo.yaml

:options:

    -k, --key=N
        Path in <files.yaml>, separated by "/". [default: /]

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
from .. import YamlGetItem
from .. import CopyToRemote
from .. import RsyncToRemote
from .. import ShelephantCopy
from .. import ShelephantCopySSH


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-k', '--key', required=False, default='/')
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
        parser.add_argument('args', nargs=2, default=['shelephant_dump.yaml', 'shelephant_hostinfo.yaml'])
        args = parser.parse_args()

        source = args.args[0]
        hostinfo = args.args[1]
        data = YamlRead(hostinfo)
        key = list(filter(None, args.key.split('/')))
        files = YamlGetItem(source, key)
        src_dir = os.path.dirname(source)
        dest_dir = data['prefix']

        if 'host' not in data:

            ShelephantCopy(
                copy_function = shutil.copy2,
                files = files,
                src_dir = src_dir,
                dest_dir = data['prefix'],
                checksum = 'checksum' in data,
                quiet = args.quiet,
                force = args.force,
                print_details = not (args.force or args.summary) or args.details,
                print_summary = not (args.force or args.details) or args.summary,
                print_all = args.details,
                theme_name = args.colors.lower(),
                yaml_hostinfo_src = args.local,
                yaml_hostinfo_dest = hostinfo)

        elif args.scp:

            ShelephantCopySSH(
                copy_function = CopyToRemote,
                host = data['host'],
                files = files,
                src_dir = src_dir,
                dest_dir = dest_dir,
                checksum = 'checksum' in data,
                quiet = args.quiet,
                force = args.force,
                print_details = not (args.force or args.summary) or args.details,
                print_summary = not (args.force or args.details) or args.summary,
                print_all = args.details,
                verbose = args.verbose,
                theme_name = args.colors.lower(),
                yaml_hostinfo_src = args.local,
                yaml_hostinfo_dest = hostinfo)

        else:

            ShelephantCopySSH(
                copy_function = RsyncToRemote,
                host = data['host'],
                files = files,
                src_dir = src_dir,
                dest_dir = dest_dir,
                checksum = 'checksum' in data,
                quiet = args.quiet,
                force = args.force,
                print_details = not (args.force or args.summary) or args.details,
                print_summary = not (args.force or args.details) or args.summary,
                print_all = args.details,
                verbose = args.verbose,
                theme_name = args.colors.lower(),
                yaml_hostinfo_src = args.local,
                yaml_hostinfo_dest = hostinfo,
                tempfilename = args.temp)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
