"""Remove files listed in a (field of a) YAML-file.
The filenames are assumed either absolute, or relative to the input YAML-file.

:usage:

    shelephant_rm [options]

    shelephant_rm [options] <input.yaml>

:argument:

    YAML-file with filenames. Default: shelephant_dump.yaml

:options:

    -k, --key=arg
        Path in the YAML-file, separated by "/". [default: /]

    -f, --force
        Remove without prompt.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
"""
import argparse
import os

import click

from .. import relpath
from .. import version
from .. import yaml
from .defaults import f_dump


def main_impl():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-k", "--key", default="/")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("input", nargs="?", default=f_dump)
    args = parser.parse_args()

    source = args.input
    key = list(filter(None, args.key.split("/")))
    files = yaml.read_item(source, key)
    prefix = os.path.dirname(source)
    files = relpath.add_prefix(prefix, files)

    if len(files) == 0:
        return 0

    for file in files:
        print(f"rm {file:s}")

    if not args.force:
        if not click.confirm("Proceed?"):
            return 1

    for file in files:
        os.remove(file)


def main():

    try:
        main_impl()
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":

    main()
