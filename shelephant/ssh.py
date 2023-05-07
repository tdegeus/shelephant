from .external import exec_cmd


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
