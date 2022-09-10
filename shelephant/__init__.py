r"""
Copy with a memory.

(c) Tom de Geus, 2021, MIT
"""
import argparse
import os
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


def _shelephant_diff_parser():
    """
    Return parser for :py:func:`shelephant_diff`.
    """

    desc = "Compare local and remote files and list differences."
    parser = argparse.ArgumentParser(description=desc)
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
    parser.add_argument("local", type=str, help="Local files to consider, see shelephant_dump.")
    parser.add_argument("remote", type=str, help="Remote files to consider, see shelephant_dump.")
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


def _shelephant_diff_catch():
    shelephant_diff(sys.argv[1:])
