import os
from collections import defaultdict

import click


def _to_tree(d):
    r"""
    Detail for: :py:fun:`filter_deepest`.
    Not part of API.
    """

    t = defaultdict(list)
    for a, *b in d:
        t[a].append(b)
    return {a: None if not (k := list(filter(None, b))) else _to_tree(k) for a, b in t.items()}


def _get_deepest_paths(d, c=[]):
    r"""
    Detail for: :py:fun:`filter_deepest`.
    Not part of API.

    See https://stackoverflow.com/a/66211932/2646505
    """
    for a, b in d.items():
        if b is None:
            yield "/".join(c + [a])
        else:
            yield from _get_deepest_paths(b, c + [a])


def filter_deepest(files: list[str]) -> list[str]:
    r"""
    Return list with only the deepest paths.

    For example::

        filter_deepest(["foo/bar/dir", "foo/bar"])
        >>> ["foo/bar/dir"]

    :param files: List of paths.
    :return: List of paths.
    """

    return list(_get_deepest_paths(_to_tree([i.split("/") for i in files])))


def dirnames(files: list[str], return_unique: bool = True) -> list[str]:
    r"""
    Get the ``os.path.dirname`` of all file paths.

    :param files: List of file paths.
    :param return_unique: Filter duplicates.
    :return: List of dirnames.
    """

    if isinstance(files, str):
        files = [files]

    ret = [os.path.dirname(filename) for filename in files]

    if not return_unique:
        return ret

    return list(set(ret))


def makedirs(dirnames: list[str], force: bool = False):
    r"""
    (Prompt and) Create directories that do not yet exist.
    This function creates parent directories if needed.

    :param dirnames: List of directory paths.
    :param force: Create directories without prompt.
    """

    if isinstance(dirnames, str):
        dirnames = [dirnames]

    dirnames = [dirname for dirname in dirnames if len(dirname) > 0]
    dirnames = [dirname for dirname in dirnames if not os.path.isdir(dirname)]

    if len(dirnames) == 0:
        return 0

    dirnames = list(set(dirnames))
    dirnames = sorted(filter_deepest(dirnames))

    if not force:
        for dirname in dirnames:
            print(f"mkdir -p {dirname:s}")
        if not click.confirm("Proceed?"):
            raise OSError("Cancelled")

    for dirname in dirnames:
        os.makedirs(dirname)
