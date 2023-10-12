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

from . import dataset
from . import local
from . import output
from . import rsync
from . import scp
from . import search
from . import ssh
from . import yaml
from ._version import version
from .external import exec_cmd

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


def shelephant_parse(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_parse_parser()
    args = parser.parse_args(args)
    data = yaml.read(args.file)
    yaml.preview(data)


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
    Dump filenames to a YAML-file.

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
    parser.add_argument("--search", type=pathlib.Path, help='Run "search" in "root".')
    parser.add_argument("-a", "--append", action="store_true", help="Append existing file.")
    parser.add_argument("-i", "--info", action="store_true", help="Add information (sha256, size).")
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
    parser.add_argument(
        "-k", "--keep", type=str, action="append", help="Keep only input matching this regex."
    )
    parser.add_argument("--fmt", type=str, help='Formatter of each line, e.g. ``"mycmd {}"``.')
    parser.add_argument(
        "-c",
        "--command",
        action="store_true",
        help="Interpret arguments as a command (instead of as filenames) an run it.",
    )
    parser.add_argument("--cwd", type=str, help="Directory to run ``--command``.")
    parser.add_argument(
        "--root", type=str, help="Root for relative paths (default: directory of output file)."
    )
    parser.add_argument("--abspath", action="store_true", help="Store as absolute paths.")
    parser.add_argument("-s", "--sort", action="store_true", help="Sort filenames.")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite output file without prompt."
    )
    parser.add_argument("-v", "--version", action="version", version=version, help="")
    parser.add_argument("files", type=str, nargs="*", help="Filenames.")

    return parser


def shelephant_dump(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_dump_parser()
    args = parser.parse_args(args)
    files = args.files
    assert not (args.command and args.cwd is not None), "Cannot use --cwd without --command."

    if args.search:
        assert len(files) == 0, "Cannot use both --search and filenames."
        assert args.root is None, "Root inferred from --search."
        assert not args.command, "Cannot use both --search and --command."
        loc = dataset.Location.from_yaml(args.search)
        loc.read(getinfo=args.info)
        root = loc.root
        files = loc.files(info=args.info)
    else:
        assert len(files) > 0, "Nothing to dump."
        if args.root:
            root = args.root
        else:
            root = args.output.parent

        if args.command:
            cmd = " ".join(files)
            files = subprocess.check_output(cmd, shell=True, cwd=args.cwd).decode("utf-8")
            files = list(filter(None, files.splitlines()))
            if args.cwd is not None:
                files = [os.path.join(args.cwd, file) for file in files]

    if args.abspath:
        files = [os.path.abspath(file) for file in files]
    elif args.search is None:
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

    if args.info and not args.search:
        files = dataset.Location(root=root, files=files).getinfo().files(info=True)

    if args.append:
        main = yaml.read(args.output)
        assert isinstance(main, list), 'Can only append a "flat" file'
        files = main + files
        args.force = True

    yaml.dump(args.output, files, args.force)


def _shelephant_cp_parser():
    """
    Return parser for :py:func:`shelephant_cp`.
    """

    desc = textwrap.dedent(
        """
        Copy files listed in a (field of a) YAML-file.
        These filenames are assumed either relative to the YAML-file or absolute.

        Usage::

            shelephant_cp <sourceinfo.yaml> <dest_dirname>
            shelephant_cp <sourceinfo.yaml> <dest_dirname_on_host> --ssh <user@host>
            shelephant_cp <sourceinfo.yaml> <destinfo.yaml>

        .. note::

            Files that are marked as equal are not touched.
        """
    )

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument("--ssh", type=str, help="SSH destination (e.g. user@host).")
    parser.add_argument("--colors", type=str, default="dark", help="Color scheme [none, dark].")
    parser.add_argument(
        "--mode",
        type=str,
        help="Use 'sha256', 'rsync', and/or 'basic' to compare files.",
        default="sha256,rsync" if shutil.which("rsync") is not None else "sha256,basic",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite without prompt.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not print progress.")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Print copy-plan and exit.")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("source", type=pathlib.Path, help="Source information.")
    parser.add_argument("dest", type=pathlib.Path, help="Destination directory/information.")
    return parser


def shelephant_cp(args: list[str], paths: list[str] = None, filter_paths: bool = True):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    :param paths:
        Instead of reading ``files`` from the source YAML-file, specify a list of paths to copy.

    :param filter_paths:
        If ``True``, ``paths`` that are not in ``files`` of the YAML-file are ignored.
        If ``False`` all ``paths`` are copied: requires ``paths`` to exist on the source.

    :return: List of changed files.

    .. note::

        For input from dataset (``paths is not None``) the storage locations can have a prefix.
        ``paths`` is a lost of paths relative to the root of the dataset.
        For example::

            foo/bar/a.txt
            foo/bar/b.txt

        Consider that

        -   ``source1`` only stores files and folders in ``foo`` .
        -   ``source2`` only stores files and folders in ``foo/bar``.

        Then::

            shelephant_cp(["source1.yml", "source2.yml"], paths=["foo/bar/a.txt", "foo/bar/b.txt"])

        will effectively run a copy of::

            copy(
                sourcepath="/path/to/root/of/source1/bar",
                destpath="/path/to/root/of/source2",
                files=["a.txt", "b.txt"],
            )

        And::

            shelephant_cp(["source2.yml", "source1.yml"], paths=["foo/bar/a.txt", "foo/bar/b.txt"])

        will effectively run a copy of::

            copy(
                sourcepath="/path/to/root/of/source2",
                destpath="/path/to/root/of/source1/bar",
                files=["a.txt", "b.txt"],
            )
    """

    parser = _shelephant_cp_parser()
    args = parser.parse_args(args)
    args.mode = args.mode.split(",")
    assert args.source.is_file(), "Source must be a file."
    assert not args.force if args.dry_run else True, "Cannot use --force with --dry-run."
    assert shutil.which("rsync") is not None or "rsync" not in args.mode, "rsync not available."
    assert "basic" not in args.mode if "rsync" in args.mode else True, "Use 'basic' or 'rsync'."

    if args.dest.is_file():
        dest = dataset.Location.from_yaml(args.dest)
    else:
        dest = dataset.Location(root=args.dest, ssh=args.ssh)

    source = dataset.Location.from_yaml(args.source)
    files = source.files(info=False)
    equal = []
    strip = None
    common_prefix, suffix_source, suffix_dest, deepest = dataset._compute_suffix(source, dest)
    source._add_suffix(suffix_source)
    dest._add_suffix(suffix_dest)
    sourcepath = source.hostpath
    destpath = dest.hostpath
    paths = [] if paths is None else paths

    if suffix_source != pathlib.Path(""):
        files = [os.path.relpath(p, suffix_source) for p in files]

    if len(paths) > 0:
        if (common_prefix / deepest) != pathlib.Path(""):
            strip = common_prefix / deepest
            paths = [os.path.relpath(p, strip) for p in paths]
            assert not any(p.startswith("..") for p in paths), "Paths not in tree."
        if filter_paths:
            files = np.intersect1d(files, paths)
        else:
            files = paths

    if source.ssh is not None or dest.ssh is not None:
        assert "rsync" in args.mode, "'rsync' required for ssh."

    if "sha256" in args.mode:
        equal = source.diff(dest)["=="]
        equal = np.intersect1d(equal, files).tolist()
        files = np.setdiff1d(files, equal, assume_unique=True).tolist()  # based on sha256

    if "rsync" in args.mode:
        status = rsync.diff(sourcepath, destpath, files)
        eq = status.pop("==", [])
        [files.remove(file) for file in eq]  # based on rsync criteria
        equal += eq
    elif "basic" in args.mode:
        status = local.diff(sourcepath, destpath, files)

    assert status.pop("<-", []) == [], "Cannot copy from destination to source."

    if len(files) == 0:
        print("Nothing to copy" if len(equal) == 0 else "All files equal")
        return []

    if not args.force:
        status["=="] = equal
        output.copyplan(status, colors=args.colors)
        if args.dry_run:
            return []
        if not click.confirm("Proceed?"):
            raise OSError("Cancelled")

    if "rsync" in args.mode:
        rsync.copy(sourcepath, destpath, files, progress=not args.quiet)
    else:
        local.copy(sourcepath, destpath, files, progress=not args.quiet)

    if strip is None:
        return files

    return list(map(str, [strip / i for i in files]))


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
        """
        Move files listed in a (field of a) YAML-file.
        These filenames are assumed either relative to the YAML-file or absolute.

        Usage::

            shelephant_mv <sourceinfo.yaml> <dest_dirname>
        """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument("--colors", type=str, default="dark", help="Color scheme [none, dark].")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite without prompt.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not print progress.")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Print copy-plan and exit.")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("source", type=pathlib.Path, help="Source information.")
    parser.add_argument("dest", type=pathlib.Path, help="Destination directory.")
    return parser


def shelephant_mv(args: list[str], paths: list[str] = None):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    :param paths: Paths to move (if not given, all files in source are moved).
    """

    parser = _shelephant_mv_parser()
    args = parser.parse_args(args)
    assert args.source.is_file(), "Source must be a file."
    assert args.dest.is_dir(), "Destination must be a directory."
    assert not args.force if args.dry_run else True, "Cannot use --force with --dry-run."

    source = dataset.Location.from_yaml(args.source)
    files = source.files(info=False)
    assert source.ssh is None, "Cannot move from remote."
    assert source.prefix is None, "prefix not supported."
    if paths is not None:
        files = np.intersect1d(files, paths).tolist()
    sourcepath = source.hostpath
    destpath = args.dest
    status = local.diff(sourcepath, destpath, files)
    assert status.pop("<-", []) == [], "Cannot move from destination to source"

    if len(files) == 0:
        print("Nothing to move")
        return

    if not args.force:
        output.copyplan(status, colors=args.colors)
        if args.dry_run:
            return
        if not click.confirm("Proceed?"):
            raise OSError("Cancelled")

    local.move(sourcepath, destpath, files, progress=not args.quiet)


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
        """
        Remove files listed in a (field of a) YAML-file.
        These filenames are assumed either relative to the YAML-file or absolute.

        Usage::

            shelephant_rm <sourceinfo.yaml>
        """
    )

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument("-f", "--force", action="store_true", help="Remove without prompt.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not print progress.")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Print copy-plan and exit.")
    parser.add_argument("--verbose", action="store_true", help="Print commands (only SSH remote).")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("source", type=pathlib.Path, help="Source information.")
    return parser


def shelephant_rm(args: list[str], paths: list[str] = None):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    :param paths: Paths to remove (if not given, all files in source are removed).
    """

    parser = _shelephant_rm_parser()
    args = parser.parse_args(args)
    assert args.source.is_file(), "Source must be a file."
    assert not args.force if args.dry_run else True, "Cannot use --force with --dry-run."

    source = dataset.Location.from_yaml(args.source)
    files = source.files(info=False)
    assert source.prefix is None, "prefix not supported."
    if paths is not None:
        files = np.intersect1d(files, paths).tolist()

    if len(files) == 0:
        print("Nothing to remove")
        return

    if not args.force:
        for file in files:
            print(f"rm {file:s}")
        if args.dry_run:
            return
        if not click.confirm("Proceed?"):
            raise OSError("Cancelled")

    if source.ssh is None:
        return local.remove(source.hostpath, files, progress=not args.quiet)

    with ssh.tempdir(source.ssh) as remote, search.tempdir():
        files = [str(source.root / i) for i in files]
        pathlib.Path("remove.txt").write_text("\n".join(files))
        shutil.copy(pathlib.Path(__file__).parent / "_remove.py", "script.py")
        hostpath = f'{source.ssh:s}:"{str(remote):s}"'
        scp.copy(".", hostpath, ["script.py", "remove.txt"], progress=False, verbose=args.verbose)
        exec_cmd(
            f'ssh {source.ssh:s} "cd {str(remote)} && {source.python} script.py"',
            verbose=args.verbose,
        )


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
        """
        Collect information about a remote directory (on a remote SSH host).
        This information is stored in a YAML-file (default: ``shelephant_hostinfo.yaml``)::

            root: <path>      # relative to the YAML-file, or absolute
            ssh: <user@host>  # (optional) remote SSH host
            dump: <dump>      # (optional, excludes "search") yaml-file to read list of files from
            search:           # (optional, excludes "dump") search information, must be set by hand
                - ...
            files:            # (optional) list of files (from "search" / "dump", or set by hand)
                - ...

        Usage:

        1.  Create *hostinfo*::

                # set "root"
                shelephant_hostinfo <path>

                # set "root" and "ssh"
                shelephant_hostinfo <path> --ssh <user@host>

                # set "root" (and "ssh") and "dump", and update "files"
                shelephant_hostinfo <path> --dump [shelephant_dump.yaml]
                shelephant_hostinfo <path> --dump [shelephant_dump.yaml] --ssh <user@host>

        2.  Update *hostinfo* (update "files")::

                # update "files" based on "dump" or "search"
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
        "-u", "--update", action="store_true", help='Update "files" based on "dump" or "search".'
    )
    parser.add_argument("-i", "--info", action="store_true", help="Add information (sha256, size).")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite output.")
    parser.add_argument("--verbose", action="store_true", help="Print commands (only SSH remote).")
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
        assert str(args.output) == f_hostinfo, "No customisation allowed in --update mode."
        assert args.dump is None, "No customisation allowed in --update mode."
        assert args.ssh is None, "No customisation allowed in --update mode."
        loc = dataset.Location.from_yaml(args.path)
        args.output = args.path
        args.force = True
    else:
        loc = dataset.Location(root=args.path, ssh=args.ssh)
        if args.dump:
            loc.dump = args.dump

    loc.read(verbose=args.verbose)
    if args.info:
        loc.getinfo(verbose=args.verbose)
    loc.to_yaml(args.output, force=args.force)


def _shelephant_diff_parser():
    """
    Return parser for :py:func:`shelephant_diff`.
    """

    desc = textwrap.dedent(
        """
        Compare local and remote files and list differences.

        Usage::
            shelephant_diff <sourceinfo.yaml> <dest_dirname>
            shelephant_diff <sourceinfo.yaml> <destinfo.yaml>
            shelephant_diff <sourceinfo.yaml> <destinfo.yaml> --filter "->"
            shelephant_diff <sourceinfo.yaml> <destinfo.yaml> --filter "?=, !="
            shelephant_diff <sourceinfo.yaml> <destinfo.yaml> -o <diff.yaml>

        Note that if filter contains only one operation the output YAML-file will be a list.
        """
    )

    desc = ""

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument("--ssh", type=str, help="SSH destination (e.g. user@host).")
    parser.add_argument("--colors", type=str, default="dark", help="Color scheme [none, dark].")
    parser.add_argument(
        "--mode", type=str, help="Use 'sha256', 'rsync', or 'basic'.", default="sha256"
    )
    parser.add_argument("--sort", type=str, help="Sort printed table by column.")
    parser.add_argument("--table", type=str, default="SINGLE_BORDER", help="Select print style.")
    parser.add_argument("--filter", type=str, help="Filter to direction (separated by ',').")
    parser.add_argument("-o", "--output", type=pathlib.Path, help="Dump as YAML file.")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite output.")
    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("source", type=pathlib.Path, help="Source information.")
    parser.add_argument("dest", type=pathlib.Path, help="Destination directory/information.")
    return parser


def shelephant_diff(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _shelephant_diff_parser()
    args = parser.parse_args(args)
    args.mode = args.mode.split(",")
    assert args.source.is_file(), "Source must be a file."
    assert len(args.mode) == 1, "Only one mode allowed."
    assert shutil.which("rsync") is not None or "rsync" not in args.mode, "rsync not available."

    source = dataset.Location.from_yaml(args.source)
    files = source.files(info=False)

    if args.dest.is_file():
        dest = dataset.Location.from_yaml(args.dest)
    else:
        dest = dataset.Location(root=args.dest, ssh=args.ssh)

    if "sha256" in args.mode:
        status = source.diff(dest)
    elif "rsync" in args.mode:
        left = source.diff(dest)["<-"]
        [files.remove(file) for file in left]
        status = rsync.diff(source.hostpath, dest.hostpath, files)
        status["<-"] = left
    elif "basic" in args.mode:
        assert source.ssh is None and dest.ssh is None, "Use 'rsync' or 'sha256' mode with SSH."
        status = local.diff(source.hostpath, dest.hostpath, files)
    else:
        raise ValueError(f"Unknown mode '{args.mode}'.")

    if args.filter:
        keys = [key.strip() for key in args.filter.split(",")]
        keys = [key for key in keys if key in status]
        status = {key: status[key] for key in keys}

    for key in list(status.keys()):
        if len(status[key]) == 0:
            del status[key]

    if args.output:
        if len(status) == 1:
            status = status[list(status.keys())[0]]
        yaml.dump(args.output, status, force=args.force)
        return

    out = prettytable.PrettyTable()
    if args.table == "PLAIN_COLUMNS":
        out.set_style(prettytable.PLAIN_COLUMNS)
    elif args.table == "SINGLE_BORDER":
        out.set_style(prettytable.SINGLE_BORDER)
    out.field_names = ["source", "sync", "dest"]
    out.align["source"] = "l"
    out.align["sync"] = "c"
    out.align["dest"] = "l"

    left = status.pop("->", [])
    right = status.pop("<-", [])
    equal = status.pop("==", [])

    for key in status:
        for item in status[key]:
            out.add_row([item, key, item])

    for item in left:
        out.add_row([item, "->", ""])

    for item in right:
        out.add_row(["", "<-", item])

    for item in equal:
        out.add_row([item, "==", item])

    if args.sort is None:
        print(out.get_string())
    else:
        print(out.get_string(sortby=args.sort))


def _shelephant_main_parser():
    """
    Return parser for :py:func:`shelephant`.
    """

    desc = textwrap.dedent(
        """
        Available commands:

        =========== ======================================================================
        command     description
        =========== ======================================================================
        init        Initialize a new dataset.
        add         Add storage location to dataset.
        remove      Remove storage location from dataset.
        update      Update dataset.
        status      Show status of files.
        info        Show global information about dataset.
        lock        Lock as storage location.
        cp          Copy files from one location to another.
        mv          Move files from one location to another (both local).
        rm          Remove files from one location.
        pwd         Print equivalent directory in the storage location.
        git         Run git command on the database directory (``.shelephant``).
        gitignore   Add all symbolic links at ``.shelephant`` to dataset's ``.gitignore``.
        =========== ======================================================================
        """
    )

    class MyFmt(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.MetavarTypeHelpFormatter,
    ):
        pass

    choices = [
        "init",
        "add",
        "remove",
        "update",
        "status",
        "info",
        "lock",
        "cp",
        "mv",
        "rm",
        "pwd",
        "git",
        "gitignore",
    ]
    parser = argparse.ArgumentParser(formatter_class=MyFmt, description=desc)
    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("command", type=str, choices=choices, help="Command to run.")
    return parser


def _shelephant_main():
    assert len(sys.argv) >= 2, "No command given."
    parser = _shelephant_main_parser()
    args = parser.parse_args([sys.argv[1]])

    if args.command == "init":
        dataset.init(sys.argv[2:])
    elif args.command == "add":
        dataset.add(sys.argv[2:])
    elif args.command == "remove":
        dataset.remove(sys.argv[2:])
    elif args.command == "update":
        dataset.update(sys.argv[2:])
    elif args.command == "status":
        dataset.status(sys.argv[2:])
    elif args.command == "info":
        dataset.info(sys.argv[2:])
    elif args.command == "cp":
        dataset.cp(sys.argv[2:])
    elif args.command == "mv":
        dataset.mv(sys.argv[2:])
    elif args.command == "rm":
        dataset.rm(sys.argv[2:])
    elif args.command == "pwd":
        dataset.pwd(sys.argv[2:])
    elif args.command == "lock":
        dataset.lock(sys.argv[2:])
    elif args.command == "git":
        dataset.git(sys.argv[2:])
    elif args.command == "gitignore":
        dataset.gitignore(sys.argv[2:])
    else:
        raise ValueError(f"Unknown command '{sys.argv[1]}'.")


def _shelephant_parse_main():
    shelephant_parse(sys.argv[1:])


def _shelephant_cp_main():
    shelephant_cp(sys.argv[1:])


def _shelephant_mv_main():
    shelephant_mv(sys.argv[1:])


def _shelephant_rm_main():
    shelephant_rm(sys.argv[1:])


def _shelephant_dump_main():
    shelephant_dump(sys.argv[1:])


def _shelephant_hostinfo_main():
    shelephant_hostinfo(sys.argv[1:])


def _shelephant_diff_main():
    shelephant_diff(sys.argv[1:])
