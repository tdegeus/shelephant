'''shelephant_extract
    Extract a field from a YAML-file.

    Unless you use --no-path, the function assumes that all data are paths,
    and changes all relative paths from being relative to <input.yaml>
    to being relative to --output.

Usage:
    shelephant_extract [options] <input.yaml>
    shelephant_extract [options] <input.yaml> <key>...

Arguments:
    input.yaml      The file to read.
    key             The keys to read from the file.

Options:
    -o, --output=N  Output file. (default: <input.yaml>)
        --no-path   Do not interpret data as paths.
    -s, --squash    Squash fields into a single field.
    -f, --force     Overwrite output file without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import os
import mergedeep
import functools

from .. import __version__
from .. import YamlGetItem
from .. import YamlDump
from .. import ChangeRootOfRelativePaths
from .. import Squash


def main():

    args = docopt.docopt(__doc__, version=__version__)
    input_dir = os.path.dirname(args['<input.yaml>'])
    output = args['--output'] if args['--output'] else args['<input.yaml>']
    output_dir = os.path.dirname(output)
    data = {}

    if len(args['<key>']) == 0:
        args['<key>'] = ['/']

    for key in args['<key>']:
        key = list(filter(None, key.split('/')))
        files = YamlGetItem(args['<input.yaml>'], key)
        if not args['--no-path']:
            files = ChangeRootOfRelativePaths(files, input_dir, output_dir)
        if len(args['<key>']) == 1:
            YamlDump(output, files, args['--force'])
            return 0
        container = functools.reduce(lambda x, y: {y: x}, key[:-1], {key[-1]: files})
        mergedeep.merge(data, container)

    if args['--squash']:
        data = Squash(data)

    YamlDump(output, data, args['--force'])

if __name__ == '__main__':

    main()
