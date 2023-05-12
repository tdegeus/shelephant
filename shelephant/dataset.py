import hashlib
import os
import pathlib

import numpy as np
import tqdm

from . import path
from . import scp
from . import yaml


def _sha256(filename: str | pathlib.Path) -> str:
    """
    Get sha256 of a file.

    :param str filename: File-path.
    :return: SHA256 hash.
    """
    with open(filename, "rb", buffering=0) as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class Location:
    """
    Location information:

    *   :py:attr:`Location.root`: The root directory.
    *   :py:attr:`Location.ssh` (optional): ``[user@]host``
    *   :py:attr:`Location.dump` (optional): Location of "dump" file -- file with list of files.
    *   :py:attr:`Location.search` (optional): Command to search for files.
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
        self.dump = None
        self.search = None

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
        self._has_sha256 = [False for _ in self._files]
        self._has_size = [False for _ in self._files]
        self._sha256 = [None for _ in self._files]
        self._size = [None for _ in self._files]

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
            raise NotImplementedError

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
    def hostname(self) -> str:
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

    def read(self):
        """
        Read files from location.
            -   If ``dump`` is set, read from dump file.
            -   If ``search`` is set, search for files.
        """
        if self.dump is None and self.search is None:
            return

        assert not (self.dump is not None and self.search is not None)

        if self.dump is not None:
            if self.ssh is None:
                return self._read_files(yaml.read(self.root / self.dump))

            with path.tempdir():
                scp.copy(self.hostname, ".", [self.dump], progress=False)
                return self._read_files(yaml.read(self.dump))

        raise NotImplementedError

    def getinfo(self, sha256: bool = True, size: bool = True, progress: bool = False):
        """
        Compute sha256 and size for files.

        :param sha256: Get sha256.
        :param size: Get size.
        :param progress: Show progress bar.
        """

        self._clear_info()

        if self.ssh is None:
            for i, file in enumerate(tqdm.tqdm(self._files, disable=not progress)):
                if sha256:
                    self._sha256[i] = _sha256(self.root / file)
                    self._has_sha256[i] = True
                if size:
                    self._size[i] = os.path.getsize(self.root / file)
                    self._has_size[i] = True
            return self

        raise NotImplementedError

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
