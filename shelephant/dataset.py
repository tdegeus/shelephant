import json
import pathlib
import shutil

import numpy as np

from . import info
from . import scp
from . import search
from . import ssh
from . import yaml
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
        a = np.argsort(self._files)
        b = np.argsort(other._files)

        return (
            np.all(np.array(self._files)[a] == np.array(other._files)[b])
            and np.all(np.array(self._sha256)[a] == np.array(other._sha256)[b])
            and np.all(np.array(self._size)[a] == np.array(other._size)[b])
            and np.all(np.array(self._has_sha256)[a] == np.array(other._has_sha256)[b])
            and np.all(np.array(self._has_size)[a] == np.array(other._has_size)[b])
        )

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

    def read(self, verbose: bool = False):
        """
        Read files from location.
            -   If ``dump`` is set, read from dump file.
            -   If ``search`` is set, search for files.

        :param verbose: Print progress (only relevant if ``ssh`` is set).
        """
        if self.dump is None and self.search is None:
            return

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
