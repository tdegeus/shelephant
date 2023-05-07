r"""
Copy with a memory.

(c) Tom de Geus, 2021, MIT
"""
import argparse
import hashlib
import os
import pathlib
import re
import subprocess
import sys

import numpy as np
import prettytable

from . import checksum
from . import convert
from . import detail
from . import path
from . import relpath
from . import rich
from . import rsync
from . import scp
from . import ssh
from . import yaml
from ._version import version
from ._version import version_tuple
from .cli.defaults import f_dump
from .cli.defaults import f_hostinfo


def sha256(filename: str | pathlib.Path) -> str:
    """
    Get sha256 of a file.

    :param str filename: File-path.
    :return: SHA256 hash.
    """
    with open(filename, "rb", buffering=0) as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _shelephant_dump_parser():
    """
    Return parser for :py:func:`shelephant_dump`.
    """

    desc = "Dump filenames to a YAML-file."
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        "-o", "--output", type=pathlib.Path, default=f_dump, help="Output YAML-file."
    )
    parser.add_argument("-a", "--append", action="store_true", help="Append existing file.")
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Add information (sha256, size, modified date).",
    )
    parser.add_argument(
        "-e", "--exclude", type=str, action="append", help="Exclude files matching this pattern."
    )
    parser.add_argument(
        "-E",
        "--exclude-extension",
        type=str,
        action="append",
        default=[],
        help='Exclude files based on extension (e.g. ".bak").',
    )
    parser.add_argument("--fmt", type=str, help='Formatter of each line, e.g. ``"mycmd {}"``.')
    parser.add_argument(
        "-c",
        "--command",
        action="store_true",
        help="Interpret arguments as command (instead of as filenames).",
    )
    parser.add_argument("-k", "--keep", type=str, action="append", help="Select files using regex.")
    parser.add_argument("--cwd", type=str, help="Directory to run the command in.")
    parser.add_argument(
        "--root", type=str, help="Root for relative paths (default: directory of output file)."
    )
    parser.add_argument(
        "--abspath", action="store_true", help="Store absolute paths (default: relative)."
    )
    parser.add_argument("-s", "--sort", action="store_true", help="Sort filenames.")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite output file without prompt."
    )
    parser.add_argument("-v", "--version", action="version", version=version, help="")
    parser.add_argument("files", nargs="+", help="Filenames.")

    return parser


def shelephant_dump(args: list[str]):
    """
    Command-line tool, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_dump_parser()
    args = parser.parse_args(args)
    files = args.files

    if args.root:
        root = args.root
    else:
        root = args.output.parent

    if args.command:
        cmd = " ".join(files)
        files = subprocess.check_output(cmd, shell=True, cwd=args.cwd).decode("utf-8").split("\n")
        files = list(filter(None, files))
        if args.cwd is not None:
            files = [os.path.join(args.cwd, file) for file in files]

    if args.abspath:
        files = [os.path.abspath(file) for file in files]
    else:
        files = [os.path.relpath(file, root) for file in files]

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

    if args.exclude_extension:
        files = [file for file in files if pathlib.Path(file).suffix not in args.exclude_extension]

    if args.sort:
        files = sorted(files)

    if args.fmt:
        files = [args.fmt.format(file) for file in files]

    if args.info:
        files = [
            {
                "path": file,
                "sha256": sha256(file),
                "size": os.path.getsize(file),
                "modified": os.path.getmtime(file),
            }
            for file in files
        ]

    if args.append:
        main = yaml.read(args.output)
        assert type(main) == list, 'Can only append a "flat" file'
        files = main + files
        args.force = True

    yaml.dump(args.output, files, args.force)


def _shelephant_diff_parser():
    """
    Return parser for :py:func:`shelephant_diff`.
    """

    desc = "Compare local and remote files and list differences."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite output.")
    parser.add_argument("--yaml", type=str, help="Dump as YAML file.")
    parser.add_argument("--sort", type=str, help="Sort printed table by column.")
    parser.add_argument("--table", type=str, default="SINGLE_BORDER", help="Select print style.")
    parser.add_argument("--checksum", action="store_true", help="Check sums.")
    parser.add_argument("--get-new", type=str, help="Save to get '<-' files.")
    parser.add_argument("--get-diff", type=str, help="Save to get ''!=' files.")
    parser.add_argument("--get-all", type=str, help="Save to get '<-' and '!=' files.")
    parser.add_argument("--send-new", type=str, nargs=2, help="Save to send '<-' files.")
    parser.add_argument("--send-diff", type=str, nargs=2, help="Save to send ''!=' files.")
    parser.add_argument("--send-all", type=str, nargs=2, help="Save to send '<-' and '!=' files.")
    parser.add_argument(
        "local", type=str, nargs="?", default=f_dump, help="Local files, see shelephant_dump."
    )
    parser.add_argument(
        "remote",
        type=str,
        nargs="?",
        default=f_hostinfo,
        help="Remote files, see shelephant_hostinfo.",
    )
    return parser


def shelephant_diff(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_diff_parser()
    args = parser.parse_args(args)

    local = yaml.read(args.local)
    remote = yaml.read(args.remote)

    if type(local) is list:
        local = {"files": local, "prefix": os.path.dirname(args.local), "list": True}
    if type(remote) is list:
        remote = {"files": remote, "prefix": os.path.dirname(args.remote), "list": True}

    for field in [local, remote]:
        if "host" in field:
            field["dirname"] = field["host"] + ":" + field["prefix"]
        else:
            field["dirname"] = field["prefix"]

        if len(field["dirname"]) == 0:
            field["dirname"] = "."

        field["files"] = np.array(field["files"])

    ret = {}

    to_remote = rsync.diff(
        source_dir=local["dirname"],
        dest_dir=remote["dirname"],
        files=local["files"],
        checksum=args.checksum,
    )
    ret["=="] = list(local["files"][to_remote["skip"]])
    ret["!="] = list(local["files"][to_remote["overwrite"]])
    ret["->"] = list(local["files"][to_remote["create"]])

    from_remote = rsync.diff(
        source_dir=remote["dirname"],
        dest_dir=local["dirname"],
        files=remote["files"],
        checksum=args.checksum,
    )
    ret["=="] += list(remote["files"][from_remote["skip"]])
    ret["!="] += list(remote["files"][from_remote["overwrite"]])
    ret["<-"] = list(remote["files"][from_remote["create"]])

    for key in ["==", "!="]:
        ret[key] = [str(i) for i in np.unique(ret[key])]
    for key in ["->", "<-"]:
        ret[key] = [str(i) for i in ret[key]]

    stop = False

    for filename, value in zip(
        [args.get_new, args.get_diff, args.get_all], [ret["<-"], ret["!="], ret["<-"] + ret["!="]]
    ):
        if filename is not None:
            stop = True
            tmp = {"files": value}
            for key in ["host", "prefix"]:
                if key in remote:
                    tmp[key] = remote[key]
            yaml.dump(filename, tmp, force=args.force)

    for filename, value in zip(
        [args.send_new, args.send_diff, args.send_all],
        [ret["->"], ret["!="], ret["->"] + ret["!="]],
    ):
        if filename is not None:
            assert "host" not in local, "Not supported by shelephant_send."
            assert len(os.path.dirname(args.local)) == 0, "Not supported by shelephant_send."
            stop = True

            yaml.dump(filename[0], value, force=args.force)

            tmp = {}
            for key in ["host", "prefix"]:
                if key in remote:
                    tmp[key] = remote[key]
            yaml.dump(filename[1], tmp, force=args.force)

    if args.yaml is not None:
        yaml.dump(args.yaml, ret, force=args.force)
        stop = True

    if stop:
        return 0

    out = prettytable.PrettyTable()
    if args.table == "PLAIN_COLUMNS":
        out.set_style(prettytable.PLAIN_COLUMNS)
    elif args.table == "SINGLE_BORDER":
        out.set_style(prettytable.SINGLE_BORDER)
    out.field_names = ["local", "sync", "remote"]
    out.align["local"] = "l"
    out.align["sync"] = "c"
    out.align["remote"] = "l"

    for item in ret["!="]:
        out.add_row([item, "!=", item])

    for item in ret["->"]:
        out.add_row([item, "->", ""])

    for item in ret["<-"]:
        out.add_row(["", "<-", item])

    if args.sort is None:
        print(out.get_string())
    else:
        print(out.get_string(sortby=args.sort))


def _shelephant_dump_main():
    shelephant_dump(sys.argv[1:])


def _shelephant_diff_main():
    shelephant_diff(sys.argv[1:])
