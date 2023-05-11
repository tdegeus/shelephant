import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap

import click
import numpy as np
import prettytable

from . import convert
from . import dataset
from . import local
from . import output
from . import path
from . import rsync
from . import scp
from . import ssh
from . import yaml
from ._version import version

# set filename defaults
f_hostinfo = "shelephant_hostinfo.yaml"
f_dump = "shelephant_dump.yaml"


def _shelephant_parse_parser():
    """
    Return parser for :py:func:`shelephant_parse`.
    """

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    desc = "Parse a YAML-file, and print to screen."
    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("file", type=pathlib.Path, help="File path.")
    return parser


def _shelephant_dump_parser():
    """
    Return parser for :py:func:`shelephant_dump`.
    """

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    desc = textwrap.dedent(
        """\
    Dump filenames ((relative) paths) to a YAML-file.

    .. note::

        If you have too many arguments you can hit the pipe-limit. In that case, use ``xargs``:

        .. code-block:: bash

            find . -name "*.py" | xargs shelephant_dump -o dump.yaml

        or you can use ``--command`` such that *shelephant* executes the command for you:

        .. code-block:: bash

            shelephant_dump -o dump.yaml --command find . -name '*.py'
    """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)

    parser.add_argument(
        "-o", "--output", type=pathlib.Path, default=f_dump, help="Output YAML-file."
    )
    parser.add_argument("-a", "--append", action="store_true", help="Append existing file.")
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Add information (sha256, size).",
    )
    parser.add_argument(
        "-e", "--exclude", type=str, action="append", help="Exclude input matching this pattern."
    )
    parser.add_argument(
        "-E",
        "--exclude-extension",
        type=str,
        action="append",
        default=[],
        help='Exclude input with this extension (e.g. ".bak").',
    )
    parser.add_argument("--fmt", type=str, help='Formatter of each line, e.g. ``"mycmd {}"``.')
    parser.add_argument(
        "-c",
        "--command",
        action="store_true",
        help="Interpret arguments as a command (instead of as filenames) an run it.",
    )
    parser.add_argument(
        "-k", "--keep", type=str, action="append", help="Keep only input matching this regex."
    )
    parser.add_argument("--cwd", type=str, help="Directory to run the command in.")
    parser.add_argument(
        "--root", type=str, help="Root for relative paths (default: directory of output file)."
    )
    parser.add_argument("--abspath", action="store_true", help="Store as absolute paths.")
    parser.add_argument("-s", "--sort", action="store_true", help="Sort filenames.")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite output file without prompt."
    )
    parser.add_argument("-v", "--version", action="version", version=version, help="")
    parser.add_argument("files", type=str, nargs="+", help="Filenames.")

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
        files = [{"path": file, **path.info(file)} for file in files]

    if args.append:
        main = yaml.read(args.output)
        assert type(main) == list, 'Can only append a "flat" file'
        files = main + files
        args.force = True

    yaml.dump(args.output, files, args.force)


def _shelephant_cp_parser_common(parser: argparse.ArgumentParser):
    """
    Set common parser arguments for :py:func:`shelephant_cp` and :py:func:`shelephant_mv`.
    """

    parser.add_argument("--colors", type=str, default="dark", help="Color scheme [none, dark].")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite without prompt.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not print progress.")
    parser.add_argument("--ssh", type=str, help="Remote SSH host (e.g. user@host).")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("path", type=pathlib.Path, nargs="+", help="Source/destination.")
    return parser


def _shelephant_cp_parser():
    """
    Return parser for :py:func:`shelephant_cp`.
    """

    desc = textwrap.dedent(
        """\
    Copy files listed in a (field of a) YAML-file.
    These filenames are assumed either relative to the YAML-file or absolute.

    Usage::

        shelephant_cp [source.yaml] <dest_dirname>
        shelephant_cp [source.yaml] <dest_dirname_on_host> --ssh <user@host>
        shelephant_cp [source.yaml] <hostinfo.yaml>
        shelephant_cp <source_hostinfo.yaml> <dest_hostinfo.yaml>

    whereby ``[source.yaml]`` defaults to ``shelephant_dump.yaml``.
    """
    )

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser = _shelephant_cp_parser_common(parser)
    return parser


def _interpret_common_cp(args: argparse.ArgumentParser, has_rsync: bool):
    """
    Parse / interpret common arguments for :py:func:`shelephant_cp` and :py:func:`shelephant_mv`.

    :param args: Parsed arguments.
    :param has_rsync: Whether ``rsync`` is available.
    :return: ``(files, source, dest, status)`` as follows:
        -   ``files``: List of files to copy.
        -   ``source``: Source directory (including SSH host if needed).
        -   ``dest``: Destination directory (including SSH host if needed).
        -   ``status``: Status of files::

            {
                "==": [],  # files are identical
                "->": [],  # files not on destination
                ...
            }
    """

    # interpret CL arguments

    if len(args.path) == 1:
        source = f_dump
        dest = args.path[0]
    elif len(args.path) == 2:
        source = args.path[0]
        dest = args.path[1]
    else:
        raise OSError("Too many arguments specified")

    # convert CL arguments to information

    source = dataset.Location.from_yaml(source)

    if dest.is_file():
        dest = dataset.Location.from_yaml(dest)
    elif dest.is_dir() or args.ssh is not None:
        dest = dataset.Location(root=dest)
    else:
        raise OSError("Destination must be a YAML-file or directory")

    if args.ssh is not None:
        dest.ssh = args.ssh

    if source.ssh or dest.ssh:
        assert has_rsync, "rsync not found, cannot copy over SSH"

    # check status based on specified sha256

    equal = source.diff(dest)["=="]
    files = source.files(info=False)
    for file in equal:
        files.pop(file)

    # check status of remaining files

    if has_rsync:
        status = rsync.diff(source.hostname, dest.hostname, files)
        status["=="] += equal
    else:
        status = local.diff(source.hostname, dest.hostname, files)
        status["=="] = equal

    assert status.pop("<-", []) == [], "Cannot copy from destination to source"
    return files, source.hostname, dest.hostname, status


def shelephant_cp(args: list[str]):
    """
    Command-line tool, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    has_rsync = shutil.which("rsync") is not None
    parser = _shelephant_cp_parser()
    args = parser.parse_args(args)
    files, source, dest, status = _interpret_common_cp(args, has_rsync)

    if not args.force:
        output.copyplan(status, colors=args.colors)
        if not click.confirm("Proceed?"):
            raise OSError("Cancelled")

    if has_rsync:
        rsync.copy(source, dest, files, progress=not args.quiet)
    else:
        local.copy(source, dest, files, progress=not args.quiet)


def _shelephant_mv_parser():
    """
    Return parser for :py:func:`shelephant_mv`.
    """

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    desc = textwrap.dedent(
        """\
    Move files listed in a (field of a) YAML-file.
    These filenames are assumed either relative to the YAML-file or absolute.

    Usage::

        shelephant_mv [source.yaml] <dest_dirname>

    whereby ``[source.yaml]`` defaults to ``shelephant_dump.yaml``.
    """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser = _shelephant_cp_parser_common(parser)
    parser.add_argument("--temp", action="store_true", help="Fully copy file before removing.")
    parser.add_argument(
        "--verify", action="store_true", help="Use --copy but check sha256 before removing."
    )
    return parser


def _shelephant_rm_parser():
    """
    Return parser for :py:func:`shelephant_rm`.
    """

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    desc = textwrap.dedent(
        """\
    Remove files listed in a (field of a) YAML-file.
    These filenames are assumed either relative to the YAML-file or absolute.

    Usage::

        shelephant_rm [source.yaml]

    whereby ``[source.yaml]`` defaults to ``shelephant_dump.yaml``.
    """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    return parser


def _shelephant_get_parser():
    """
    Return parser for :py:func:`shelephant_get`.
    """

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    desc = textwrap.dedent(
        """\
    Copy files from a remote directory (on a remote host) to the current directory.

    Usage::

        shelephant_get <source>
        shelephant_get <source> --ssh <user@host>
        shelephant_get [hostinfo.yaml]

    whereby ``[source.yaml]`` defaults to ``shelephant_dump.yaml``.
    """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    return parser


def _shelephant_hostinfo_parser():
    """
    Return parser for :py:func:`shelephant_hostinfo`.
    """

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    desc = textwrap.dedent(
        """\
    Collect information about a remote directory (on a remote host).
    This information is stored in a YAML-file (default: ``shelephant_hostinfo.yaml``) as follows::

        root: <path>      # relative to the YAML-file, or absolute
        ssh: <user@host>  # (optional) remote SSH host
        dump: <dump>      # (optional, excludes "search") path from which a list of files is read
        search:           # (optional, excludes "dump") search information, must be set by hand
            - ...
        files:            # (optional) list of files (from "search" / "dump", or set by hand)
            - ...

    Usage:

    1.  Create *hostinfo*::

            shelephant_hostinfo <path>
            shelephant_hostinfo <path> --ssh <user@host>
            shelephant_hostinfo <path> --dump [shelephant_dump.yaml]
            shelephant_hostinfo <path> --dump [shelephant_dump.yaml] --ssh <user@host>

    2.  Update *hostinfo*::

            shelephant_hostinfo --update [shelephant_hostinfo.yaml]
    """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument(
        "-o", "--output", type=pathlib.Path, default=f_hostinfo, help="Output YAML-file."
    )
    parser.add_argument(
        "-d",
        "--dump",
        type=pathlib.Path,
        default=None,
        nargs="?",
        const=f_dump,
        help="YAML-file containing a list of files.",
    )
    parser.add_argument("--ssh", type=str, help="Remote SSH host (e.g. user@host).")
    parser.add_argument(
        "--update", action="store_true", help='Update "files" based on "dump" or "search".'
    )
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite output.")
    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("path", type=pathlib.Path, help="Path to remote directory.")
    return parser


def shelephant_hostinfo(args: list[str]):
    """
    Command-line tool, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_hostinfo_parser()
    args = parser.parse_args(args)

    if args.update:
        assert args.output == f_hostinfo, "No customisation allowed in --update mode."
        assert args.dump is None, "No customisation allowed in --update mode."
        assert args.ssh is None, "No customisation allowed in --update mode."
        loc = dataset.Location.from_yaml(args.path)
        args.output = args.path
        args.force = True
    else:
        loc = dataset.Location(root=args.path, ssh=args.ssh)
        if args.dump:
            loc.dump = args.dump

    loc.read()
    loc.to_yaml(args.output, force=args.force)


def _shelephant_diff_parser():
    """
    Return parser for :py:func:`shelephant_diff`.
    """

    desc = "Compare local and remote files and list differences."

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
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


def _shelephant_cp_main():
    shelephant_cp(sys.argv[1:])


def _shelephant_dump_main():
    shelephant_dump(sys.argv[1:])


def _shelephant_hostinfo_main():
    shelephant_hostinfo(sys.argv[1:])


def _shelephant_diff_main():
    shelephant_diff(sys.argv[1:])
