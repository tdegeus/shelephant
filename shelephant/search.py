import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager


@contextmanager
def tempdir():
    """
    Set the cwd to a temporary directory::

        with tempdir("foo"):
            # Do something in foo
    """

    origin = pathlib.Path().absolute()
    with tempfile.TemporaryDirectory() as dirname:
        try:
            os.chdir(dirname)
            yield
        finally:
            os.chdir(origin)


@contextmanager
def cwd(dirname: pathlib.Path):
    """
    Set the cwd to a specified directory::

        with cwd("foo"):
            # Do something in foo

    :param dirname: The directory to change to.
    """
    origin = pathlib.Path().absolute()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(origin)


def _check_skip(path: str, skip: list[str]) -> bool:
    """
    Check if a path should be skipped.

    :param path: The path to check.
    :param skip: A list of regex to skip.
    :return: ``True`` if the path should be skipped.
    """
    for s in skip:
        if re.match(s, path):
            return True
    return False


def _search_rglob(rglob: str, root: str = ".", skip: list[str] = []) -> list[pathlib.Path]:
    """
    Search for files using ``rglob``.

    :param rglob: The pattern to search for.
    :param root: The root directory to search in.
    :param skip: A list of regex to skip.
    :return: A list of paths.
    """
    if isinstance(skip, str):
        skip = [skip]
    ret = []
    for path in pathlib.Path(root).rglob(rglob):
        if _check_skip(str(path), skip):
            continue
        ret.append(path)
    return ret


def _search_glob(glob: str, root: str = ".", skip: list[str] = []) -> list[pathlib.Path]:
    """
    Search for files using ``glob``.

    :param glob: The pattern to search for.
    :param root: The root directory to search in.
    :param skip: A list of regex to skip.
    :return: A list of paths.
    """
    if isinstance(skip, str):
        skip = [skip]
    ret = []
    for path in pathlib.Path(root).glob(glob):
        if _check_skip(str(path), skip):
            continue
        ret.append(path)
    return ret


def _search_exec(exec: str, skip: list[str] = []) -> list[pathlib.Path]:
    """
    Search for files using a command.

    :param exec: The command to run.
    :param skip: A list of regex to skip.
    :return: A list of paths.
    """
    if isinstance(skip, str):
        skip = [skip]
    paths = subprocess.check_output(exec, shell=True).decode("utf-8").splitlines()
    paths = list(filter(None, paths))
    ret = []
    for path in paths:
        if _check_skip(path, skip):
            continue
        ret.append(path)
    return list(map(pathlib.Path, map(os.path.normpath, ret)))


def search(*settings: dict, root: pathlib.Path = pathlib.Path(".")) -> list[pathlib.Path]:
    r"""
    Search for files using a list of settings, as follows::

        [
            {"rglob": "*.py", "skip": ["\..*", "build"]},
            {"exec": "find . -name '*.cpp'"},
        ]

    :param settings: A list of settings.
    :param root: The root directory to search in.
    :return: A list of paths.
    """
    with cwd(root):
        ret = []
        for setting in settings:
            if "rglob" in setting:
                ret += _search_rglob(**setting)
            elif "exec" in setting:
                ret += _search_exec(**setting)
            elif "glob" in setting:
                ret += _search_glob(**setting)
            else:
                raise ValueError(f"Unknown search setting: {setting}")
        return list(set(ret))


if __name__ == "__main__":
    settings = json.loads(pathlib.Path("settings.json").read_text())
    root = sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(".")
    files = search(*settings, root=pathlib.Path(root))
    pathlib.Path("files.txt").write_text("\n".join(map(str, files)))
