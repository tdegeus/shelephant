import argparse
import os
import re
import subprocess
import sys

import numpy as np

from .. import version
from .. import yaml
from .defaults import f_dump


def _shelephant_dump_parser():
    """
    Return parser for :py:func:`shelephant_dump`.
    """

    desc = "Dump filenames to a YAML-file."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-o", "--output", default=f_dump, help="Output YAML-file.")
    parser.add_argument("-a", "--append", action="store_true", help="Append existing file.")
    parser.add_argument(
        "-e", "--exclude", type=str, action="append", help="Exclude files matching this pattern."
    )
    parser.add_argument("--fmt", type=str, help='Formatter of each line, e.g. ``"mycmd {}"``.')
    parser.add_argument(
        "-c",
        "--command",
        action="store_true",
        help="Interpret the input as a command (instead of as filenames).",
    )
    parser.add_argument("-k", "--keep", type=str, action="append", help="Select files using regex.")
    parser.add_argument("--cwd", type=str, help="Directory to run the command in.")
    parser.add_argument(
        "--abspath",
        action="store_true",
        help="Store absolute paths (default: relative to the output file).",
    )
    parser.add_argument("-s", "--sort", action="store_true", help="Sort filenames.")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite output file without prompt."
    )
    parser.add_argument("-v", "--version", action="version", version=version, help="")
    parser.add_argument("file", nargs="+", help="Files to list.")
    return parser


def shelephant_dump(args: list[str]):
    """
    Command-line tool, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_dump_parser()
    args = parser.parse_args(args)

    prefix = os.path.dirname(args.output)
    files = args.file

    if args.command:
        cmd = " ".join(files)
        files = subprocess.check_output(cmd, shell=True, cwd=args.cwd).decode("utf-8").split("\n")
        files = list(filter(None, files))
        if args.cwd is not None:
            files = [os.path.join(args.cwd, file) for file in files]

    if args.abspath:
        files = [os.path.abspath(file) for file in files]
    else:
        files = [os.path.relpath(file, prefix) for file in files]

    if args.keep:
        ret = []
        for pattern in args.keep:
            ret += [file for file in files if re.match(pattern, file)]
        files = ret

    if args.exclude:
        excl = np.zeros(len(files), dtype=bool)
        for pattern in args.exclude:
            excl = np.logical_or(excl, np.array([re.match(pattern, file) for file in files]))
        files = [file for file, ex in zip(files, excl) if not ex]

    if args.sort:
        files = sorted(files)

    if args.fmt:
        files = [args.fmt.format(file) for file in files]

    if args.append:
        main = yaml.read(args.output)
        assert type(main) == list, 'Can only append a "flat" file'
        files = main + files
        args.force = True

    yaml.dump(args.output, files, args.force)


def main():
    shelephant_dump(sys.argv[1:])


if __name__ == "__main__":

    main()
