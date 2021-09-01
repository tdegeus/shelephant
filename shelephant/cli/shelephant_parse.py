"""Parse a YAML-file, and print to screen.

:usage:

    shelephant_parse <file.yaml>

:argument:

    File path.

:options:

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
"""
import argparse

from .. import version
from .. import yaml


def main_impl():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("file")
    args = parser.parse_args()

    data = yaml.read(args.file)
    yaml.view(data)


def main():

    try:
        main_impl()
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":

    main()
