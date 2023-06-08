import pathlib
import re
import subprocess
from contextlib import contextmanager

from .external import exec_cmd


def _shelephant_cachdir(hostname: str, python: str = "python3") -> str:
    """
    Return the path to the shelephant cache directory or a tempdir on a remote host.

    :param hostname: Hostname.
    :param python: Python executable (on remote).
    :return: Path to the shelephant cache directory or a tempdir on a remote host.
    """

    script = [
        "from platformdirs import user_cache_dir",
        "from pathlib import Path",
        "d = user_cache_dir('shelephant', 'tdegeus')",
        "Path(d).mkdir(exist_ok=True)",
        "print(d)",
    ]
    cmd = f"{python:s} -c \\\"{';'.join(script):s}\\\" || mktemp -d"
    cmd = f'ssh {hostname:s} "{cmd:s}"'
    ret = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True).decode("utf-8")
    return ret.strip().splitlines()[0]


@contextmanager
def _cachedir(hostname: str, cache_dir: str):
    """
    Do nothing if the cache directory is a shelephant cache directory.
    Otherwise, remove the cache directory on exit.

        with _cachedir(hostname, cache_dir) as cachdir_tempdir:
            print(cachdir_tempdir)
    """

    try:
        if re.match(r".*shelephant.*", str(cache_dir)):
            rm = None
            yield pathlib.Path(cache_dir)
        else:
            rm = cache_dir
            yield pathlib.Path(cache_dir.strip())
    finally:
        if rm is not None:
            cmd = f"ssh {hostname:s} rm -rf {cache_dir:s}"
            exec_cmd(cmd, verbose=False)


def has_keys_set(hostname: str) -> bool:
    """
    Check if the ssh keys are set for a given host.

    :param hostname: Hostname.
    :return: ``True`` if the host can be accessed without password.
    """

    cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=5 {hostname:s} echo ok"

    try:
        ret = exec_cmd(cmd, verbose=False)
    except subprocess.CalledProcessError:
        return False

    if ret.strip() == "ok":
        return True

    return False


def is_dir(hostname: str, path: str, verbose: bool = False) -> bool:
    """
    Check if a directory exists on a remote system. Uses ``ssh``.

    :param hostname: Hostname.
    :param path: Directory (path on hostname).
    :param verbose: Verbose commands.
    :return: ``True`` if the file exists, ``False`` otherwise.
    """

    ret = exec_cmd(
        f'ssh {hostname:s} "test -d {str(path):s} && echo found || echo not found"', verbose
    )
    if ret.strip() == "found":
        return True
    return False


def is_file(hostname: str, path: str, verbose: bool = False) -> bool:
    """
    Check if a file exists on a remote system. Uses ``ssh``.

    :param hostname: Hostname.
    :param path: Filename (path on hostname).
    :param verbose: Verbose commands.
    :return: ``True`` if the file exists, ``False`` otherwise.
    """

    ret = exec_cmd(
        f'ssh {hostname:s} "test -f {str(path):s} && echo found || echo not found"', verbose
    )
    if ret.strip() == "found":
        return True
    return False


@contextmanager
def tempdir(hostname: str):
    """
    Create a temporary directory on a remote system. Uses ``ssh``.

        with tempdir("localhost") as remote_tempdir:
            print(remote_tempdir)
    """

    try:
        cmd = f"ssh {hostname:s} mktemp -d"
        tempdir = exec_cmd(cmd, verbose=False)
        yield pathlib.Path(tempdir.strip())
    finally:
        cmd = f"ssh {hostname:s} rm -rf {tempdir:s}"
        exec_cmd(cmd, verbose=False)
