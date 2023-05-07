import pathlib

import numpy as np

from .yaml import read


def _filelist_to_dict(data: list, dummy_sha256: int | str) -> dict:
    """
    Convert input to::

        {
            "file1": {"sha256": ...},
            "file2": {"sha256": ...},
            ...
        }

    :param data: Input data.
    :param dummy_sha256: Dummy sha256 value to use.
    :return: Dictionary, see above.
    """

    if type(data) == dict:
        for key in data:
            data[key].setdefault("sha256", dummy_sha256)
        return data

    if type(data) == str:
        return {data: {"sha256": dummy_sha256}}

    ret = {}

    for item in data:
        if type(item) == str:
            ret[item] = {"sha256": dummy_sha256}
        else:
            item.setdefault("sha256", dummy_sha256)
            ret[item.pop("path")] = item

    return ret


def interpret_file(filename: str) -> tuple[dict, dict]:
    """
    Read a file and interpret it as a shelephant file.

    :param filename: Filename to read.
    :return:
        Tuple of ``(files, meta)``, with::

            files = {
                "file1": {"sha256": ...},
                "file2": {"sha256": ...},
                ...
            }

        and::

            meta = {
                "root": ...,
                ...
            }
    """

    data = read(filename)

    if type(data) == dict:
        files = data.pop("files", [])
        data.setdefault("root", pathlib.Path(filename).parent)
        return _filelist_to_dict(files, None), data

    return _filelist_to_dict(data, None), {"root": pathlib.Path(filename).parent}


def diff(a: list | dict, b: list | dict) -> dict:
    """
    Compare the database entries of two locations.
    The location information (``a`` and ``b``) are specified as follows::

        a = ["file1", "file2", ...]

    or::

        a = [
            {"path": "file1", "sha256": ...},
            {"path": "file2", "sha256": ...},
            ...
        ]

    or::

        a = {
            "file1": {"sha256": ...},
            "file2": {"sha256": ...},
            ...
        }

    :param a: List of files.
    :param a: List of files.

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

    a = _filelist_to_dict(a, -1)
    b = _filelist_to_dict(b, -2)

    files_a = list(a.keys())
    files_b = list(b.keys())

    inboth = [str(i) for i in np.intersect1d(files_a, files_b)]
    ret = {
        "->": [str(i) for i in np.setdiff1d(files_a, files_b)],
        "<-": [str(i) for i in np.setdiff1d(files_b, files_a)],
        "==": [],
        "?=": [],
        "!=": [],
    }

    for i in inboth:
        sa = a[i]["sha256"]
        sb = b[i]["sha256"]
        if sa == sb:
            ret["=="].append(i)
        elif sa == -1 or sb == -2:
            ret["?="].append(i)
        else:
            ret["!="].append(i)

    return ret
