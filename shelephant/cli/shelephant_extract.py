'''shelephant_extract
    Extract a field from a YAML-file.

    Unless you use --no-path, the function assumes that all data are paths,
    and changes all relative paths from being relative to <input.yaml>
    to being relative to --output.

:usage:

    shelephant_extract [options] <input.yaml> [<key>...]

:arguments:

    <input.yaml>
        The file to read.

    <key>
        The keys to read from the file.

:options:

    -o, --output=N
        Output file. (default: <input.yaml>)

    --no-path
        Do not interpret data as paths.

    -s, --squash
        Squash fields into a single field.

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
import mergedeep
import functools

from .. import version
from .. import YamlGetItem
from .. import YamlDump
from .. import ChangeRootOfRelativePaths
from .. import Squash


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-o', '--output', required=False)
        parser.add_argument(      '--no-path', required=False, action='store_true')
        parser.add_argument('-s', '--squash', required=False, action='store_true')
        parser.add_argument('-f', '--force', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('input')
        parser.add_argument('key', nargs='*')
        args = parser.parse_args()

        input_dir = os.path.dirname(args.input)
        output = args.output if args.output else args.input
        output_dir = os.path.dirname(output)
        data = {}

        if len(args.key) == 0:
            args.key = ['/']

        for key in args.key:
            key = list(filter(None, key.split('/')))
            files = YamlGetItem(args.input, key)
            if not args.no_path:
                files = ChangeRootOfRelativePaths(files, input_dir, output_dir)
            if len(args.key) == 1:
                YamlDump(output, files, args.force)
                return 0
            container = functools.reduce(lambda x, y: {y: x}, key[:-1], {key[-1]: files})
            mergedeep.merge(data, container)

        if args.squash:
            data = Squash(data)

        YamlDump(output, data, args.force)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
