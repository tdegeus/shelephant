r"""
FIle operations.

(c) Tom de Geus, 2021, MIT
"""
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


def filter_deepest(paths):
    r"""
    Return list with only the deepest paths.

    For example::

        filter_deepest(["foo/bar/dir", "foo/bar"])
        >>> ["foo/bar/dir"]

    :type paths: list of str
    :param paths: List of paths.

    :rtype: list of str
    :return: List of paths.
    """

    return list(_get_deepest_paths(_to_tree([i.split("/") for i in paths])))


def check_allisfile(paths):
    r"""
    Check that all paths point to existing files.
    Uses: ``os.path.isfile``.

    :param list paths: List of file paths.
    :throw: IOError
    """

    if type(paths) == str:
        paths = [paths]

    for path in paths:
        if not os.path.isfile(path):
            raise OSError(f'"{path:s}" does not exist')


def dirnames(paths, return_unique=True):
    r"""
    Get the ``os.path.dirname`` of all file paths.

    :param list paths: List of file paths.
    :param bool return_unique: Filter duplicates.
    :return: List of dirnames.
    """

    if type(paths) == str:
        paths = [paths]

    ret = [os.path.dirname(path) for path in paths]

    if not return_unique:
        return ret

    return list(set(ret))


def overwrite(paths, force=False):
    r"""
    (Prompt and) List files that will be overwritten if created.

    :param list paths: List of file paths.
    :param bool force: If ``True`` the user is prompted to overwrite.
    :return: List of overwritten files.
    """

    if type(paths) == str:
        paths = [paths]

    ret = [path for path in paths if os.path.isfile(path)]

    if force or len(ret) == 0:
        return ret

    print("Files exist:")
    print("\n".join(ret))
    if not click.confirm("Overwrite?"):
        raise OSError("Cancelled")

    return ret


def makedirs(dirnames, force=False):
    r"""
    (Prompt and) Create directories that do not yet exist.
    This function creates parent directories if needed.

    :param bool force: Create directories without prompt.
    """

    if type(dirnames) == str:
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
