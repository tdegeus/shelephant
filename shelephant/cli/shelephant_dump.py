'''shelephant_dump
    Dump filenames to a YAML-file.

:usage:

    shelephant_dump [options] <file>...

:arguments:

    Files to dump. By default the filenames are written relative to the output file.

:options:

    -o, --output=N
        Output YAML-file. [default: shelephant_dump.yaml]

    -a, --append
        Append existing file.

    -c, --command
        Interpret the input as a command (instead of as filenames).

    --abspath
        Store absolute paths (default: relative to the output file).

    -s, --sort
        Sort filenames.

    -f, --force
        Overwrite output file without prompt.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import argparse
import os
import subprocess

from .. import version
from .. import YamlDump
from .. import YamlRead


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-o', '--output', required=False, default='shelephant_dump.yaml')
        parser.add_argument('-a', '--append', required=False, action='store_true')
        parser.add_argument('-c', '--command', required=False, action='store_true')
        parser.add_argument(      '--abspath', required=False, action='store_true')
        parser.add_argument('-s', '--sort', required=False, action='store_true')
        parser.add_argument('-f', '--force', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('file', nargs='+')
        args = parser.parse_args()

        prefix = os.path.dirname(args.output)
        files = args.file

        if args.command:
            command = ' '.join(files)
            files = sorted(list(filter(None, subprocess.check_output(
                command, shell=True).decode('utf-8').split('\n'))))

        if args.abspath:
            files = [os.path.abspath(file) for file in files]
        else:
            files = [os.path.relpath(file, prefix) for file in files]

        if args.sort:
            files = sorted(files)

        if args.append:

            main = YamlRead(args.output)
            if type(main) != list:
                raise IOError('Can only append a "flat" file')

            files = main + files
            args.force = True

        YamlDump(args.output, files, args.force)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
