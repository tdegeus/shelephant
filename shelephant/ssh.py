r"""
Query using ssh.

(c) Tom de Geus, 2021, MIT
"""
from .external import exec_cmd


def file_exists(host, source, verbose=False):
    r"""
    Check if a file exists on a remote system. Uses ``ssh``.
    """

    cmd = 'ssh {host:s} test -f "{source:s}" && echo found || echo not found'.format(
        host=host, source=source
    )

    ret = exec_cmd(cmd, verbose)

    if ret == "found":
        return True

    return False
