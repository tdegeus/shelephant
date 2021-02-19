'''shelephant_checksum
    Get checksum of files listed in a (field of a) YAML-file.
    The filenames are assumed either absolute, or relative to the input YAML-file.

Usage:
    shelephant_checksum [options]
    shelephant_checksum [options] <input.yaml>

Arguments:
    YAML-file with file-paths. Default: shelephant_dump.yaml

Options:
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

import docopt
import os

from .. import version
from .. import YamlGetItem
from .. import YamlDump
from .. import PrefixPaths
from .. import GetChecksums


def main():

    try:

        args = docopt.docopt(__doc__, version=version)
        source = args['<input.yaml>'] if args['<input.yaml>'] else 'shelephant_dump.yaml'
        key = list(filter(None, args['--key'].split('/')))
        files = YamlGetItem(source, key)
        prefix = os.path.dirname(source)
        files = PrefixPaths(prefix, files)
        data = GetChecksums(files, args['--local'], hybrid=True, progress=not args['--quiet'])
        YamlDump(args['--output'], data, args['--force'])

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
