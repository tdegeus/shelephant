import argparse
import json
import os
import pathlib
import shutil
import textwrap

import numpy as np
import prettytable

from . import cli
from . import info
from . import scp
from . import search
from . import ssh
from . import yaml
from ._version import version
from .external import exec_cmd


class Location:
    """
    Location information.

    Attributes:

    *   :py:attr:`Location.root`: The root directory.
    *   :py:attr:`Location.ssh` (optional): ``[user@]host``
    *   :py:attr:`Location.python` (optional): The python executable on the ``ssh`` host.
    *   :py:attr:`Location.dump` (optional): Location of "dump" file -- file with list of files.
    *   :py:attr:`Location.search` (optional):
        Commands to search for files, see :py:func:`shelephant.search.search`.
    *   :py:func:`Location.files`: List of files.

    Initialize:

    *   Read from yaml file::

            location = Location.from_yaml("location.yaml")

    *   Create from scratch::

            location = Location(root="~/data"[, ssh="user@host"])
    """

    def __init__(self, root: str | pathlib.Path, ssh: str = None, files: list[str] = []) -> None:
        self.root = pathlib.Path(root)
        self.ssh = ssh
        self.python = "python3"
        self.dump = None
        self.search = None

        if ssh is not None:
            assert self.root.is_absolute(), "root must be absolute path when using ssh"

        if type(files) == list:
            self._files = files
            self._clear_info()
        elif type(files) == str:
            self._files = [files]
            self._clear_info()
        elif type(files) == dict:
            self._files = list(files.keys())
            self._clear_info()
            for i, file in enumerate(self._files):
                self._has_sha256[i] = "sha256" in files[file]
                self._has_size[i] = "size" in files[file]
                self._sha256[i] = files[file].get("sha256", None)
                self._size[i] = files[file].get("size", None)
        else:
            raise TypeError(f"Unknown type of files: {type(files)}")

    def _clear_info(self):
        """
        Clear file info.
        """
        self._has_sha256 = [False] * len(self._files)
        self._has_size = [False] * len(self._files)
        self._sha256 = [None] * len(self._files)
        self._size = [None] * len(self._files)
        return self

    def _read_files(self, files: list):
        """
        Read files from list.

        :param files: List of files.
        """
        self._files = []
        self._has_sha256 = []
        self._has_size = []
        self._sha256 = []
        self._size = []

        for item in files:
            if type(item) == str:
                self._files.append(item)
                self._has_sha256.append(False)
                self._has_size.append(False)
                self._sha256.append(None)
                self._size.append(None)
            else:
                self._files.append(item["path"])
                self._has_sha256.append("sha256" in item)
                self._has_size.append("size" in item)
                self._sha256.append(item.get("sha256", None))
                self._size.append(item.get("size", None))

        return self

    def __eq__(self, other):
        """
        Check if all files and information are equal.

        :param other: Other location.
        :return: True if equal, False otherwise.
        """
        if len(self._files) != len(other._files):
            return False

        a = np.argsort(self._files)
        b = np.argsort(other._files)

        return (
            np.all(np.equal(np.array(self._files)[a], np.array(other._files)[b]))
            and np.all(np.equal(np.array(self._sha256)[a], np.array(other._sha256)[b]))
            and np.all(np.equal(np.array(self._size)[a], np.array(other._size)[b]))
            and np.all(np.equal(np.array(self._has_sha256)[a], np.array(other._has_sha256)[b]))
            and np.all(np.equal(np.array(self._has_size)[a], np.array(other._has_size)[b]))
        )

    def __iadd__(self, other):
        assert self.root == other.root, "root must be equal"
        assert self.ssh == other.ssh, "ssh must be equal"
        self._files += other._files
        self._has_sha256 += other._has_sha256
        self._has_size += other._has_size
        self._sha256 += other._sha256
        self._size += other._size
        self.search = None
        self.dump = None
        return self

    def __add__(self, other):
        ret = Location(root=self.root, ssh=self.ssh)
        assert ret.root == other.root, "root must be equal"
        assert ret.ssh == other.ssh, "ssh must be equal"
        ret._files = self._files + other._files
        ret._has_sha256 = self._has_sha256 + other._has_sha256
        ret._has_size = self._has_size + other._has_size
        ret._sha256 = self._sha256 + other._sha256
        ret._size = self._size + other._size
        ret.search = None
        ret.dump = None
        return ret

    @classmethod
    def from_yaml(cls, path: str | pathlib.Path):
        """
        Read from yaml file.

        :param path: Path to yaml file.
        :return: Location.
        """

        path = pathlib.Path(path)
        data = yaml.read(path)
        if type(data) == list:
            data = {"files": data}

        ret = cls(root=data.get("root", path.parent), ssh=data.get("ssh", None))
        ret.dump = data.get("dump", None)
        ret.search = data.get("search", None)
        ret._read_files(data.get("files", []))
        return ret

    def to_yaml(self, path: str | pathlib.Path, force: bool = False):
        """
        Write to yaml file.

        :param path: Path to yaml file.
        :param force: Do not prompt to overwrite file.
        """
        yaml.dump(path, self.asdict(), force=force)

    def asdict(self) -> dict:
        """
        Return as dictionary.

        :return: Dictionary.
        """

        ret = {"root": str(self.root)}

        if self.ssh is not None:
            ret["ssh"] = self.ssh

        if self.dump is not None:
            ret["dump"] = str(self.dump)

        if self.search is not None:
            ret["search"] = self.search

        if len(self._files) > 0:
            ret["files"] = self.files(info=True)

        return ret

    def files(self, info: bool = True) -> list:
        """
        Return as list of files.
        Items without sha256 and size are returned as ``str``,
        items with sha256 and size are returned as ``dict``.

        :param info: Return sha256 and size (if available).
        :return: List of files.
        """

        if not info:
            return self._files

        if not np.any(self._has_sha256) and not np.any(self._has_size):
            return self._files

        ret = []

        for i, file in enumerate(self._files):
            if self._has_sha256[i] and self._has_size[i]:
                ret += [{"path": file, "sha256": self._sha256[i], "size": self._size[i]}]
            elif self._has_sha256[i]:
                ret += [{"path": file, "sha256": self._sha256[i]}]
            elif self._has_size[i]:
                ret += [{"path": file, "size": self._size[i]}]
            else:
                ret += [file]

        return ret

    @property
    def hostpath(self) -> str:
        """
        Return:

        -   ``root`` if ``ssh`` is not set.
        -   ``ssh:"root"`` if ``ssh`` is set.
        """

        if self.ssh is None:
            return str(self.root)

        return f'{self.ssh:s}:"{str(self.root):s}"'

    def sort(self, key: str = "files"):
        """
        Sort files.

        :param key: Key to sort by (files, size, sha256).
        """

        if key == "files":
            sorter = np.argsort(self._files)
        elif key == "size":
            sorter = np.argsort(self._size)
        elif key == "sha256":
            sorter = np.argsort(self._sha256)
        else:
            raise ValueError(f"Unknown key: {key}")

        self._files = np.array(self._files)[sorter].tolist()
        self._has_sha256 = np.array(self._has_sha256)[sorter].tolist()
        self._has_size = np.array(self._has_size)[sorter].tolist()
        self._sha256 = np.array(self._sha256)[sorter].tolist()
        self._size = np.array(self._size)[sorter].tolist()

        return self

    def unique(self):
        _, idx = np.unique(self._files, return_index=True)
        # TODO: check that the checksums and sizes are the same
        self._files = np.array(self._files)[idx].tolist()
        self._sha256 = np.array(self._sha256)[idx].tolist()
        self._size = np.array(self._size)[idx].tolist()
        self._has_sha256 = np.array(self._has_sha256)[idx].tolist()
        self._has_size = np.array(self._has_size)[idx].tolist()
        return self

    def isavailable(self) -> bool:
        if self.ssh is None:
            return self.root.is_dir()
        return ssh.is_dir(self.ssh, self.root)

    def remove(self, paths: list[str]):
        keep = ~np.in1d(self._files, list(map(str, paths)))
        self._files = np.array(self._files)[keep].tolist()
        self._sha256 = np.array(self._sha256)[keep].tolist()
        self._size = np.array(self._size)[keep].tolist()
        self._has_sha256 = np.array(self._has_sha256)[keep].tolist()
        self._has_size = np.array(self._has_size)[keep].tolist()

        return self

    def read(self, verbose: bool = False):
        """
        Read files from location.
            -   If ``dump`` is set, read from dump file.
            -   If ``search`` is set, search for files.

        :param verbose: Print progress (only relevant if ``ssh`` is set).
        """
        if self.dump is None and self.search is None:
            return self

        assert not (self.dump is not None and self.search is not None)

        # read from YAML dump file
        if self.dump is not None:
            if self.ssh is None:
                return self._read_files(yaml.read(self.root / self.dump))

            with search.tempdir():
                scp.copy(self.hostpath, ".", [self.dump], progress=False)
                return self._read_files(yaml.read(self.dump))

        # search for files (locally)
        if self.ssh is None:
            self._files = list(map(str, search.search(*self.search, root=self.root)))
            return self._clear_info()

        # search for files (on SSH remote host)
        with ssh.tempdir(self.ssh) as remote, search.tempdir():
            shutil.copy(pathlib.Path(__file__).parent / "search.py", "script.py")
            with open("settings.json", "w") as f:
                json.dump(self.search, f)

            host = f'{self.ssh:s}:"{str(remote):s}"'
            scp.copy(".", host, ["script.py", "settings.json"], progress=False, verbose=verbose)
            exec_cmd(
                f'ssh {self.ssh:s} "cd {str(remote)} && {self.python} script.py {str(self.root)}"',
                verbose=verbose,
            )
            scp.copy(host, ".", ["files.txt"], progress=False, verbose=verbose)
            self._files = pathlib.Path("files.txt").read_text().splitlines()
            return self._clear_info()

    def getinfo(self, progress: bool = False, verbose: bool = False):
        """
        Compute sha256 and size for files.

        :param progress: Show progress bar (only relevant if ``ssh`` is not set).
        :param verbose: Show verbose output (only relevant if ``ssh`` is set).
        """

        self._clear_info()

        # locally
        if self.ssh is None:
            hash, size = info.getinfo([self.root / f for f in self._files], progress=progress)
            self._sha256 = hash
            self._size = size
            self._has_sha256 = [True] * len(self._files)
            self._has_size = [True] * len(self._files)
            return self

        # on SSH remote host
        with ssh.tempdir(self.ssh) as remote, search.tempdir():
            shutil.copy(pathlib.Path(__file__).parent / "info.py", "script.py")
            pathlib.Path("files.txt").write_text(
                "\n".join([str(self.root / i) for i in self._files])
            )

            hostpath = f'{self.ssh:s}:"{str(remote):s}"'
            scp.copy(".", hostpath, ["script.py", "files.txt"], progress=False, verbose=verbose)
            exec_cmd(
                f'ssh {self.ssh:s} "cd {str(remote)} && {self.python} script.py"', verbose=verbose
            )
            scp.copy(hostpath, ".", ["sha256.txt", "size.txt"], progress=False, verbose=verbose)

            self._sha256 = pathlib.Path("sha256.txt").read_text().splitlines()
            self._has_sha256 = [True] * len(self._sha256)

            self._size = list(map(int, pathlib.Path("size.txt").read_text().splitlines()))
            self._has_size = [True] * len(self._size)

        return self

    def diff(self, other) -> dict:
        """
        Compare the database entries of two locations.

        .. warning::

            The information is taken from the database.
            There are no checks that that information if up to date.

        :param other: Other location.
        :return:
            Dictionary with differences::

                {
                    "==" : [ ... ], # in a and b, equal sha256
                    "?=" : [ ... ], # in a and b, unknown sha256
                    "!=" : [ ... ], # in a and b, different sha256
                    "->" : [ ... ], # in a not in b
                    "<-" : [ ... ], # in b not in a
                }
        """

        inboth = [str(file) for file in np.intersect1d(self._files, other._files)]
        ret = {
            "->": [str(file) for file in np.setdiff1d(self._files, other._files)],
            "<-": [str(file) for file in np.setdiff1d(other._files, self._files)],
            "==": [],
            "?=": [],
            "!=": [],
        }

        index_self = {file: i for i, file in enumerate(self._files)}
        index_other = {file: i for i, file in enumerate(other._files)}

        for file in inboth:
            ia = index_self[file]
            ib = index_other[file]

            if self._has_sha256[ia] and other._has_sha256[ib]:
                if self._sha256[ia] == other._sha256[ib]:
                    ret["=="].append(file)
                else:
                    ret["!="].append(file)
            else:
                ret["?="].append(file)

        return ret


# https://stackoverflow.com/a/68994012/2646505
def _search_upwards_dir(dirname: str) -> pathlib.Path:
    """
    Search in the current directory and all directories above it for a directory
    with a particular name.

    :param dirname: The name of the directory to look for.
    :return: The location of the first directory found or None, if none was found.
    """
    d = pathlib.Path.cwd()
    root = pathlib.Path(d.root)

    while d != root:
        attempt = d / dirname
        if attempt.is_dir():
            return attempt
        d = d.parent

    return None


def _init_parser():
    """
    Return parser for :py:func:`shelephant init`.
    """

    desc = textwrap.dedent(
        """
        Initialize a shelephant database by creating a directory ``.shelephant``
        with an 'empty' database. Use ``shelephant add`` to add storage locations.
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
    parser.add_argument("--version", action="version", version=version)
    return parser


def init(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _init_parser()
    args = parser.parse_args(args)
    sdir = pathlib.Path(".shelephant")
    assert not sdir.is_dir(), '".shelephant" directory already exists'
    sdir.mkdir()
    (sdir / "data").mkdir()
    (sdir / "storage").mkdir()
    (sdir / "unavailable").symlink_to("dead-link")
    (sdir / "symlinks.yaml").write_text("")
    yaml.dump(sdir / "storage.yaml", ["here"])
    yaml.dump(sdir / "storage" / "here.yaml", {"root": ".."})


def _add_parser():
    """
    Return parser for :py:func:`shelephant add`.
    """

    desc = textwrap.dedent(
        """
        Add a storage location to the database.
        The database in ``.shelephant`` is updated as follows:

            -   The ``name`` is added to ``.shelephant/storage.yaml``.

            -   A file ``.shelephant/storage/<name>.yaml`` is created with the search settings
                and the present state of the storage location.

            -   A symlink ``.shelephant/data/<name>`` is created to the storage location.
                (if ``--ssh`` is given, the symlink points to a dead link).
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

    parser.add_argument("name", type=str, help="Name of the storage location.")
    parser.add_argument("root", type=str, help="Path to the storage location.")
    parser.add_argument("--ssh", type=str, help="SSH host (e.g. user@host).")
    parser.add_argument("--rglob", type=str, help="Search pattern for ``Path(root).rglob(...)``.")
    parser.add_argument("--glob", type=str, help="Search pattern for ``Path(root).glob(...)``.")
    parser.add_argument("--exec", type=str, help="Command to run from ``root``.")
    parser.add_argument("--skip", type=str, action="append", help="Pattern to skip (Python regex).")
    parser.add_argument("--shallow", action="store_true", help="Do not compute checksums.")
    parser.add_argument("--version", action="version", version=version)
    return parser


def add(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _add_parser()
    args = parser.parse_args(args)
    sdir = _search_upwards_dir(".shelephant")

    storage = yaml.read(sdir / "storage.yaml")
    assert args.name not in storage, f"storage location '{args.name}' already exists"

    root = pathlib.Path(args.root)
    if not root.is_absolute() and not args.ssh:
        root = pathlib.Path(os.path.relpath(root.absolute(), sdir))

    with search.cwd(sdir):
        loc = Location(root=root, ssh=args.ssh)
        s = []
        d = {}
        if args.skip is not None:
            d["skip"] = args.skip
        if args.rglob:
            s.append({"rglob": args.rglob, **d})
        if args.glob:
            s.append({"glob": args.glob, **d})
        if args.exec:
            s.append({"exec": args.exec, **d})
        if len(s) > 0:
            loc.search = s

        loc.to_yaml(f"storage/{args.name}.yaml")
        yaml.dump("storage.yaml", storage + [args.name], force=True)

        if root.is_absolute() and not args.ssh:
            pathlib.Path(f"data/{args.name}").symlink_to(root)
        elif not args.ssh:
            pathlib.Path(f"data/{args.name}").symlink_to(pathlib.Path("..") / root)
        else:
            pathlib.Path(f"data/{args.name}").symlink_to(pathlib.Path("..") / "unavailable")

        if args.shallow:
            update([args.name, "--shallow"])
        else:
            update([args.name])


def _remove_parser():
    """
    Return parser for :py:func:`shelephant rm`.
    """

    desc = textwrap.dedent(
        """
        Remove a storage location to the database.
        The database in ``.shelephant`` is updated as follows:

            -   The ``name`` is removed from ``.shelephant/storage.yaml``.
            -   ``.shelephant/storage/<name>.yaml`` is removed.
            -   The symlink ``.shelephant/data/<name>`` is removed.
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

    parser.add_argument("name", type=str, help="Name of the storage location.")
    parser.add_argument("--version", action="version", version=version)
    return parser


def remove(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _remove_parser()
    args = parser.parse_args(args)
    sdir = _search_upwards_dir(".shelephant")

    storage = yaml.read(sdir / "storage.yaml")
    assert args.name in storage, f"storage location '{args.name}' does not exist"
    storage.remove(args.name)
    yaml.dump(sdir / "storage.yaml", storage, force=True)
    os.remove(sdir / "storage" / f"{args.name}.yaml")
    (sdir / "data" / args.name).unlink()
    update([])


def _update_parser():
    """
    Return parser for :py:func:`shelephant update`.
    """

    desc = textwrap.dedent(
        """
        Update the database.
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

    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("--shallow", action="store_true", help="Do not compute checksums.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update state of all (available) storage locations and --prune.",
    )
    parser.add_argument(
        "name", type=str, nargs="*", help="Update state of storage location(s) and  --prune."
    )
    return parser


def update(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _update_parser()
    args = parser.parse_args(args)
    sdir = _search_upwards_dir(".shelephant")

    if args.all:
        args.name = yaml.read(sdir / "storage.yaml")
        # args.name.remove("here")

    with search.cwd(sdir):
        symlinks = list(map(pathlib.Path, yaml.read("symlinks.yaml", [])))

        for name in args.name:
            if name == "here":
                path = "storage/here.yaml"
                Location.from_yaml(path).read().remove(symlinks).to_yaml(path, force=True)
                continue

            loc = Location.from_yaml(f"storage/{name}.yaml")
            if loc.isavailable():
                loc.read()
                if not args.shallow:
                    loc.getinfo()
                loc.to_yaml(f"storage/{name}.yaml", force=True)

        storage = yaml.read("storage.yaml")
        storage.remove("here")
        files = {}
        for name in storage[::-1]:
            loc = Location.from_yaml(pathlib.Path("storage") / f"{name}.yaml")
            if loc.ssh is None:
                for f in loc.files(info=False):
                    if (loc.root / f).is_file():
                        files[pathlib.Path(f)] = pathlib.Path("data") / name
                    else:
                        files[pathlib.Path(f)] = "unavailable"
            else:
                for f in loc.files(info=False):
                    files[pathlib.Path(f)] = "unavailable"

        with search.cwd(sdir / ".."):
            for f in symlinks:
                if f.exists() and not f.is_symlink():
                    raise RuntimeError(f"{f} managed by shelephant, but not a symlink")

            for f in symlinks:
                if f.is_symlink():
                    f.unlink()

            rm = []
            for f in files:
                if f.is_file():
                    rm.append(f)
            for f in rm:
                files.pop(f)

            if len(rm) > 0:
                print("Local files conflicting with dataset. No links are created for these files:")
                print("\n".join(map(str, rm)))

            yaml.dump(".shelephant/symlinks.yaml", list(map(str, files)), force=True)

            for f in files:
                f.parent.mkdir(parents=True, exist_ok=True)
            for f in files:
                s = pathlib.Path(os.path.relpath(".shelephant", f.parent)) / files[f] / f
                f.symlink_to(s)


def _cp_parser():
    """
    Return parser for :py:func:`shelephant cp`.
    """

    desc = textwrap.dedent(
        """
        Copy files between storage locations.
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

    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("--colors", type=str, default="dark", help="Color scheme [none, dark].")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite without prompt.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not print progress.")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Print copy-plan and exit.")
    parser.add_argument("source", type=str, help="name of the source.")
    parser.add_argument("destination", type=str, help="name of the destination.")
    parser.add_argument("path", type=str, nargs="+", help="path(s) to copy.")
    return parser


def cp(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _cp_parser()
    args = parser.parse_args(args)
    sdir = _search_upwards_dir(".shelephant")
    assert args.source != "here", "Cannot copy from here."
    assert args.destination != "here", "Cannot copy to here."
    base = sdir.parent
    paths = [os.path.relpath(path, base) for path in args.path]

    with search.cwd(sdir):
        opts = [f"storage/{args.source}.yaml", f"storage/{args.destination}.yaml"]
        opts += ["--colors", args.colors]
        opts += ["--force"] if args.force else []
        opts += ["--quiet"] if args.quiet else []
        opts += ["--dry-run"] if args.dry_run else []
        cli.shelephant_cp(opts, paths)

    update([args.source, args.destination])


def _status_parser():
    """
    Return parser for :py:func:`shelephant status`.
    """

    desc = textwrap.dedent(
        """
        Status of the storage locations.
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

    parser.add_argument("--version", action="version", version=version)
    parser.add_argument("--min-copies", type=int, help="Show files with minimal number of copies.")
    parser.add_argument("--copies", type=int, help="Show files with specific number of copies.")
    parser.add_argument("--ne", action="store_true", help="Show files with unequal copies.")
    parser.add_argument("--na", action="store_true", help="Show files unavailable somewhere.")
    parser.add_argument("--unknown", action="store_true", help="Show files with unknown sha256.")
    parser.add_argument("--table", type=str, default="SINGLE_BORDER", help="Select print style.")
    parser.add_argument("--in-use", type=str, help="Select storage location in use.")
    parser.add_argument("--output", type=pathlib.Path, help="Dump to YAML file.")
    parser.add_argument("--copy", type=str, nargs=2, help="Copy file selection.")
    parser.add_argument("path", type=str, nargs="*", help="Filter to paths.")
    return parser


def status(args: list[str]):
    """
    Command-line tool, see ``--help``.

    :param args: Command-line arguments (should be all strings).
    """

    parser = _status_parser()
    args = parser.parse_args(args)
    sdir = _search_upwards_dir(".shelephant")
    base = sdir.parent
    paths = [os.path.relpath(path, base) for path in args.path]

    if args.output is not None:
        raise NotImplementedError

    if args.copy is not None:
        raise NotImplementedError

    with search.cwd(sdir):
        symlinks = np.sort(yaml.read("symlinks.yaml", []))
        storage = yaml.read("storage.yaml")
        storage.remove("here")
        extra = Location.from_yaml("storage/here.yaml").files(info=False)

        sha = "" * np.ones((len(symlinks), len(storage)), dtype=object)
        inuse = "----" * np.ones((len(symlinks)), dtype=object)

        for iname, name in enumerate(storage[::-1]):
            loc = Location.from_yaml(pathlib.Path("storage") / f"{name}.yaml")
            sorter = np.argsort(loc._files)
            idx = np.searchsorted(symlinks, np.array(loc._files)[sorter])
            s = np.array(loc._sha256)[sorter]
            h = ~np.array(loc._has_sha256, dtype=bool)
            if np.any(h):
                s[h] = "?="
            sha[idx, -1 - iname] = s
            if loc.isavailable():
                inuse[idx] = name

    def _reduce(ret):
        missing = np.any(ret == "")
        unknown = np.any(ret == "?=")
        _, a, b = np.unique(ret, return_index=True, return_inverse=True)
        n = a.size
        if missing:
            n -= 1
            missing = ["x"]
        else:
            missing = []

        if unknown:
            n -= 1
            unknown = ["?="]
        else:
            unknown = []

        if n == 1:
            names = ["=="]
        else:
            names = [str(i) for i in range(1, n + 1)]

        names = np.array(missing + names + unknown, dtype=object)
        return names[np.arange(a.size)[b]]

    sha = np.apply_along_axis(_reduce, 1, sha)
    sha = np.hstack((np.array([symlinks]).T, inuse.reshape(-1, 1), sha))

    e = "x" * np.ones((len(extra), sha.shape[1]), dtype=object)
    e[:, 0] = extra
    e[:, 1] = "here"
    sha = np.vstack((sha, e))

    if args.min_copies is not None:
        sha = sha[np.sum(sha[:, 2:] == "==", axis=1) >= args.min_copies]
    if args.copies is not None:
        sha = sha[np.sum(sha[:, 2:] == "==", axis=1) == args.copies]
    if args.ne:
        sha = sha[np.sum(sha[:, 2:] == "1", axis=1) > 0]
    if args.na:
        sha = sha[np.sum(sha[:, 2:] == "x", axis=1) > 0]
    if args.unknown:
        sha = sha[np.sum(sha[:, 2:] == "?=", axis=1) > 0]
    if args.in_use is not None:
        sha = sha[sha[:, 1] == args.in_use]

    if len(paths) > 0:
        idx = np.intersect1d(paths, sha[:, 0], return_indices=True)[2]
        sha = sha[idx]

    out = prettytable.PrettyTable()
    if args.table == "PLAIN_COLUMNS":
        out.set_style(prettytable.PLAIN_COLUMNS)
    elif args.table == "SINGLE_BORDER":
        out.set_style(prettytable.SINGLE_BORDER)

    out.field_names = ["path", "in use"] + storage

    out.align["path"] = "l"
    out.align["in use"] = "l"
    for name in storage:
        out.align[name] = "c"

    for row in sha:
        out.add_row(row)

    print(out.get_string())


def git(args: list[str]):
    """
    Run git from ``.shelephant`` directory.
    """
    with search.cwd(_search_upwards_dir(".shelephant")):
        exec_cmd(f"git {' '.join(args)}")
