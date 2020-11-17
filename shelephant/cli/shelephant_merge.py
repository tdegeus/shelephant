'''shelephant_merge
    Merge a YAML file into another YAML file.

    Unless you use --no-path, the function assumes that all data are paths,
    and changes all relative paths from being relative to <branch.yaml> or <main.yaml>
    to being relative to --output.

Usage:
    shelephant_merge [options] <branch.yaml> <main.yaml>

Options:
    -o, --output=N  Output file. (default: <main.yaml>)
        --replace   Replace fields in <main.yaml> that are also in <branch.yaml>. (default: append)
        --skip      Skip fields in <branch.yaml> that are also in <main.yaml>
        --no-path   Do not interpret data as paths.
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
from . import ChangeRootRelativePaths

def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)


def main():

    args = docopt.docopt(__doc__, version=__version__)
    main = ReadYaml(args['<main.yaml>'])
    branch = ReadYaml(args['<branch.yaml>'])
    output = args['--output'] if args['--output'] else args['<main.yaml>']
    outdir = os.path.dirname(output)

    if not args['--no-path']:

        paths = [os.path.dirname(args['<main.yaml>']), os.path.dirname(args['<branch.yaml>'])]

        for var, path in zip([main, branch], paths):
            if type(var) == list:
                ChangeRootRelativePaths(var, path, outdir, in_place=True)
            elif type(var) == dict:
                for key, value in recursive_items(var):
                    ChangeRootRelativePaths(value, path, outdir, in_place=True)
            else:
                Error('Files have an incompatible structure')

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

    YamlDump(output, main, args['--force'])

if __name__ == '__main__':

    main()
