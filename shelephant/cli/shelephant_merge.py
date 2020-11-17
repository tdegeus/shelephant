'''shelephant_merge
    Merge a YAML file into another YAML file.

Usage:
    shelephant_merge [options] <branch.yaml> <main.yaml>

Options:
    -o, --output=N  Output file. (default: <main.yaml>)
    -r, --replace   Replace fields in <main.yaml> that are also in <branch.yaml>. (default: append)
    -s, --skip      Skip fields in <branch.yaml> that are also in <main.yaml>
    -f, --force     Overwrite without prompt.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import mergedeep
import os
import sys

from .. import __version__
from . import ReadYaml
from . import YamlDump
from . import Error


def main():

    args = docopt.docopt(__doc__, version=__version__)
    main = ReadYaml(args['<main.yaml>'])
    branch = ReadYaml(args['<branch.yaml>'])

    if type(main) == list and type(branch) == list:

        if args['--skip']:
            pass
        elif args['--replace']:
            main = branch
        else:
            main += branch

    elif type(main) == dict and type(branch) == dict:

        from mergedeep import merge, Strategy

        if args['--skip']:
            mergedeep.merge(branch, main, strategy=mergedeep.Strategy.REPLACE)
            main = branch
        elif args['--replace']:
            mergedeep.merge(main, branch, strategy=mergedeep.Strategy.REPLACE)
        else:
            mergedeep.merge(main, branch, strategy=mergedeep.Strategy.ADDITIVE)

    else:

        Error('Files have an incompatible structure')

    YamlDump(args['--output'] if args['--output'] else args['<main.yaml>'], main, args['--force'])

if __name__ == '__main__':

    main()
