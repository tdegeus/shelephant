r"""
Copy using scp.

(c) Tom de Geus, 2021, MIT
"""
from .external import exec_cmd


def from_remote(host, source, dest, verbose=False):
    r"""
    Copy a file from a remote system. Uses ``scp -p``.
    """

    cmd = f"scp -p {host:s}:{source:s} {dest:s}"

    exec_cmd(cmd, verbose)


def to_remote(host, source, dest, verbose=False):
    r"""
    Copy a file to a remote system. Uses ``scp -p``.
    """

    cmd = f"scp -p {source:s} {host:s}:{dest:s}"

    exec_cmd(cmd, verbose)
