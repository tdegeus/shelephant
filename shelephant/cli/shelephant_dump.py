'''shelephant_dump
    Dump filenames to a YAML-file.

Usage:
    shelephant_dump [options] <file>...

Argument(s):
    Files to dump. By default the filenames are written relative to the output file.

Options:
    -o, --output=N      Output YAML-file. [default: shelephant_dump.yaml]
    -a, --append        Append existing file.
    -c, --command       Interpret the input as a command (instead of as filenames).
        --abspath       Store absolute paths (default: relative to the output file).
    -s, --sort          Sort filenames.
    -f, --force         Overwrite output file without prompt.
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import os
import subprocess

from .. import __version__
from .. import YamlDump
from .. import YamlRead


def main():

    args = docopt.docopt(__doc__, version=__version__)
    prefix = os.path.dirname(args['--output'])
    files = args['<file>']

    if args['--command']:
        command = ' '.join(files)
        files = sorted(list(filter(None, subprocess.check_output(
            command, shell=True).decode('utf-8').split('\n'))))

    if args['--abspath']:
        files = [os.path.abspath(file) for file in files]
    else:
        files = [os.path.relpath(file, prefix) for file in files]

    if args['--sort']:
        files = sorted(files)

    if args['--append']:

        main = YamlRead(args['--output'])
        if type(main) != list:
            Error('Can only append a "flat" file')

        files = main + files
        args['--force'] = True

    YamlDump(args['--output'], files, args['--force'])


if __name__ == '__main__':

    main()
