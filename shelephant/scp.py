import os

import tqdm

from .external import exec_cmd


def copy(
    source_dir: str,
    dest_dir: str,
    files: list[str],
    options: str = "-p",
    verbose: bool = False,
    progress: bool = True,
):
    """
    Copy files using *scp*.

    :param source_dir: Source directory. If remote: ``[user@]host:path``.
    :param dest_dir: Source directory. If remote: ``[user@]host:path``.
    :param files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param options: Options passed to ``scp``.
    :param verbose: Verbose commands.
    :param progress: Show progress bar.
    """

    for file in tqdm.tqdm(files, disable=not progress):
        cmd = f"scp {options:s} {os.path.join(source_dir, file):s} {os.path.join(dest_dir, file):s}"
        exec_cmd(cmd, verbose)
