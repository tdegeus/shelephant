'''shelephant_dump
    Dump filenames to a YAML-file.

Usage:
    shelephant_dump [options] <file>...

Options:
    -o, --output=N      Output YAML-file. [default: shelephant_dump.yaml]
    -c, --command       Interpret the input as a command (instead of as filenames).
    -a, --abspath       Store absolute paths (default: relative to the output file).
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
from . import YamlDump


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

    YamlDump(args['--output'], files, args['--force'])


if __name__ == '__main__':

    main()
