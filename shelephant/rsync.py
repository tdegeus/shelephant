r"""
Copy & query using *rsync*.

(c) Tom de Geus, 2021, MIT
"""
import os
import re
import subprocess
import tempfile

import numpy as np
import tqdm

from .external import exec_cmd


def _rsync(source_dir, dest_dir, files, verbose=False, progress=True):
    r"""
    Copy files to a destination using ``rsync -a --files-from``.

    :param str source_dir: Source directory.
    :param str dest_dir: Source directory.
    :param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param bool verbose: Verbose commands.
    :param bool progress: Show progress bar.
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_file = os.path.join(temp_dir, "rsync.txt")

        with open(temp_file, "w") as file:
            file.write("\n".join(files))

        # Run without printing output

        if not progress:

            cmd = 'rsync -a --files-from="{files:s}" "{source_dir:s}" "{dest_dir:s}"'.format(
                source_dir=source_dir, dest_dir=dest_dir, files=temp_file
            )

            return exec_cmd(cmd, verbose)

        # Run while printing output

        cmd = 'rsync -aP --files-from="{files:s}" "{source_dir:s}" "{dest_dir:s}"'.format(
            source_dir=source_dir, dest_dir=dest_dir, files=temp_file
        )

        if verbose:
            print(cmd)

        pbar = tqdm.tqdm(total=len(files))
        sbar = tqdm.tqdm(unit="B", unit_scale=True)

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

        for line in iter(process.stdout.readline, b""):
            line = line.decode("utf-8")
            if re.match(r"(.*)(xf)([e]?)(r\#)([0-9])(.*)(to\-ch)([e]?[c]?)(k\=)([0-9])(.*)", line):
                e = int(list(filter(None, line.split(" ")))[-6].replace(",", ""))
                pbar.update()
                sbar.update(e)


def from_remote(
    hostname,
    source_dir,
    dest_dir,
    files,
    verbose=False,
    progress=True,
):
    r"""
    Copy files from a remote system. Uses: ``rsync -a --files-from``.

    :param str hostname: Hostname.
    :param str source_dir: Source directory.
    :param str dest_dir: Source directory.
    :param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param bool verbose: Verbose commands.
    :param bool progress: Show progress bar.
    """

    return _rsync(
        source_dir=hostname + ":" + source_dir,
        dest_dir=dest_dir,
        files=files,
        verbose=verbose,
        progress=progress,
    )


def to_remote(
    hostname,
    source_dir,
    dest_dir,
    files,
    verbose=False,
    progress=True,
):
    r"""
    Copy files to a remote system. Uses: ``rsync -a --files-from``.

    :param str hostname: Hostname.
    :param str source_dir: Source directory.
    :param str dest_dir: Source directory.
    :param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param bool verbose: Verbose commands.
    :param bool progress: Show progress bar.
    """

    return _rsync(
        source_dir=source_dir,
        dest_dir=hostname + ":" + dest_dir,
        files=files,
        verbose=verbose,
        progress=progress,
    )


def diff(
    source_dir: str,
    dest_dir: str,
    files: list[str],
    checksum: bool = False,
    verbose: bool = False,
) -> np.array:
    r"""
    Check if files are different using *rsync*.
    *rsync* uses basic criteria such as file size and creation and modification date.
    This is much faster than using checksums but is only approximate.
    See `rsync manual <https://www.samba.org/ftp/rsync/rsync.html>`_.

    :param str source_dir: Source directory.
    :param str dest_dir: Source directory.
    :param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param checksum: Use checksum to test file difference.
    :param verbose: Verbose commands.
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_file = os.path.join(temp_dir, "rsync.txt")
        files = [os.path.normpath(file) for file in files]

        with open(temp_file, "w") as file:
            file.write("\n".join(files))

        # Run without printing output

        opt = "-nai"

        if checksum:
            opt += "c"

        cmd = 'rsync {opt:s} --files-from="{files:s}" "{source_dir:s}" "{dest_dir:s}"'.format(
            source_dir=source_dir, dest_dir=dest_dir, files=temp_file, opt=opt
        )

        lines = list(filter(None, exec_cmd(cmd, verbose).split("\n")))
        lines = [line for line in lines if line[1] == "f"]

        if len(lines) == 0:
            return {
                "skip": np.ones((len(files)), dtype=np.bool),
                "create": np.zeros((len(files)), dtype=np.bool),
                "overwrite": np.zeros((len(files)), dtype=np.bool),
            }

        check_paths = [line.split(" ")[1] for line in lines]
        mode = np.zeros((len(check_paths)), dtype=np.int16)

        for i, line in enumerate(lines):
            # todo: split send `<` and recieve `>`?
            # ref: https://stackoverflow.com/a/12037164/2646505
            if line[0] == ">" or line[0] == "<":
                if line[2] == "+":
                    mode[i] = 1  # create
                else:
                    mode[i] = 2  # overwrite
            elif line[0] == ".":
                pass
            else:
                raise OSError(f'Unknown cryptic output "{line:s}"')

        sorter = np.argsort(files)
        source_paths = np.array(files, dtype=str)[sorter]

        i = np.argsort(check_paths)
        check_paths = np.array(check_paths, dtype=str)[i]
        mode = mode[i]

        test = np.in1d(source_paths, check_paths)

        idx = np.searchsorted(check_paths, source_paths)
        idx = np.where(test, idx, 0)
        ret = np.where(test, mode[idx], 0)
        ret = ret.astype(np.int16)
        out = np.empty_like(ret)
        out[sorter] = ret

        return {
            "skip": out == 0,
            "create": out == 1,
            "overwrite": out == 2,
        }
