import pathlib
import subprocess
from contextlib import contextmanager

from .external import exec_cmd


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


def file_exists(hostname: str, path: str, verbose: bool = False) -> bool:
    r"""
    Check if a file exists on a remote system. Uses ``ssh``.

    :param hostname: Hostname.
    :param path: Filename (path on hostname).
    :param verbose: Verbose commands.
    :return: ``True`` if the file exists, ``False`` otherwise.
    """

    cmd = 'ssh {hostname:s} test -f "{path:s}" && echo found || echo not found'.format(
        hostname=hostname, path=path
    )

    ret = exec_cmd(cmd, verbose)

    if ret == "found":
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
