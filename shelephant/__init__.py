r"""
Copy with a memory.

(c) Tom de Geus, 2021, MIT
"""
import argparse
import os
import sys
import tempfile

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
    parser.add_argument("--local-host", type=str, help="Host to use for local.")
    parser.add_argument("--remote-host", type=str, help="Host to use for remote.")
    parser.add_argument("--local-prefix", type=str, help="Prefix to use for local.")
    parser.add_argument("--remote-prefix", type=str, help="Prefix to use for remote.")
    parser.add_argument("--get", type=str, help="Save to get '<-' files.")
    parser.add_argument("--get-all", type=str, help="Save to get '<-' and '!=' files.")
    parser.add_argument("--send", type=str, nargs=2, help="Save to send '->' files.")
    parser.add_argument("--send-all", type=str, nargs=2, help="Save to send '->' and '!=' files.")
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
        local = {"files": local, "prefix": os.path.dirname(args.local)}
    if type(remote) is list:
        remote = {"files": remote, "prefix": os.path.dirname(args.remote)}

    if args.local_host is not None:
        local["host"] = args.local_host
    if args.remote_host is not None:
        remote["host"] = args.remote_host
    if args.local_prefix is not None:
        local["prefix"] = args.local_prefix
    if args.remote_prefix is not None:
        remote["prefix"] = args.remote_prefix

    if "host" in local:
        local_dir = local["host"] + ":" + local["prefix"]
    else:
        local_dir = local["prefix"]

    if "host" in remote:
        remote_dir = remote["host"] + ":" + remote["prefix"]
    else:
        remote_dir = remote["prefix"]

    if len(local_dir) == 0:
        local_dir = "."
    if len(remote_dir) == 0:
        remote_dir = "."

    ret = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, "rsync.txt")

        to_remote = rsync.diff(
            source_dir=local_dir,
            dest_dir=remote_dir,
            files=local["files"],
            tempfilename=temp_file,
            force=True,
            checksum=args.checksum,
        )
        files = np.array(local["files"])
        ret["=="] = list(files[to_remote["skip"]])
        ret["!="] = list(files[to_remote["overwrite"]])
        ret["->"] = list(files[to_remote["create"]])

        from_remote = rsync.diff(
            source_dir=remote_dir,
            dest_dir=local_dir,
            files=remote["files"],
            tempfilename=temp_file,
            force=True,
            checksum=args.checksum,
        )
        files = np.array(remote["files"])
        ret["=="] += list(files[from_remote["skip"]])
        ret["!="] += list(files[from_remote["overwrite"]])
        ret["<-"] = list(files[from_remote["create"]])

    for key in ["==", "!="]:
        ret[key] = [str(i) for i in np.unique(ret[key])]
    for key in ["->", "<-"]:
        ret[key] = [str(i) for i in ret[key]]

    stop = False

    if args.get is not None:
        yaml.dump(args.get, {"files": ret["<-"], **remote}, force=args.force)
        stop = True

    if args.get_all is not None:
        yaml.dump(args.get_all, {"files": ret["<-"] + ret["!="], **remote}, force=args.force)
        stop = True

    if args.send is not None:
        yaml.dump(args.send[0], ret["->"], force=args.force)
        yaml.dump(args.send[1], remote, force=args.force)
        stop = True

    if args.send_all is not None:
        yaml.dump(args.send_all[0], ret["->"] + ret["!="], force=args.force)
        yaml.dump(args.send_all[1], **remote, force=args.force)
        stop = True

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
