"""Merge a YAML-file into another YAML-file.

Unless you use --no-path, the function assumes that all data are paths,
and changes all relative paths from being relative to <branch.yaml> or <main.yaml>
to being relative to --output.

:usage:

    shelephant_merge [options] <branch.yaml> <main.yaml>

:arguments:

    <branch.yaml>
        File to merge into main.yaml.

    <main.yaml>
        Main source.

:options:

    -o, --output=arg
        Output file. (default: <main.yaml>)

    --replace
        Replace fields in <main.yaml> that are also in <branch.yaml>. (default: append)

    --skip
        Skip fields in <branch.yaml> that are also in <main.yaml>.

    --no-path
        Do not interpret data as paths.

    -f, --force
        Overwrite output file without prompt.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
"""
import argparse
import os

import mergedeep

from .. import relpath
from .. import version
from .. import yaml


def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)


def main_impl():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-o", "--output")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--skip", action="store_true")
    parser.add_argument("--no-path", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("branch")
    parser.add_argument("main")
    args = parser.parse_args()

    main = yaml.read(args.main)
    branch = yaml.read(args.branch)
    output = args.output if args.output else args.main
    output_dir = os.path.dirname(output)

    if not args.no_path:

        paths = [os.path.dirname(args.main), os.path.dirname(args.branch)]

        for var, path in zip([main, branch], paths):
            if type(var) == list:
                relpath.chroot(var, path, output_dir, in_place=True)
            elif type(var) == dict:
                for key, value in recursive_items(var):
                    relpath.chroot(value, path, output_dir, in_place=True)
            else:
                raise OSError("Files have an incompatible structure")

    if type(main) == list and type(branch) == list:

        if args.skip:
            pass
        elif args.replace:
            main = branch
        else:
            main += branch

    elif type(main) == dict and type(branch) == dict:

        if args.skip:
            mergedeep.merge(branch, main, strategy=mergedeep.Strategy.REPLACE)
            main = branch
        elif args.replace:
            mergedeep.merge(main, branch, strategy=mergedeep.Strategy.REPLACE)
        else:
            mergedeep.merge(main, branch, strategy=mergedeep.Strategy.ADDITIVE)

    else:

        raise OSError("Files have an incompatible structure")

    yaml.dump(output, main, args.force)


def main():

    try:
        main_impl()
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":

    main()
