import os
import shutil

import numpy as np
import tqdm


def remove(
    source_dir: str,
    files: list[str],
    progress: bool = True,
):
    """
    Remove files using os.remove.

    :param source_dir: Source directory
    :param dest_dir: Source directory
    :param files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param progress: Show progress bar.
    """

    for file in tqdm.tqdm(files, disable=not progress):
        os.remove(os.path.join(source_dir, file))


def move(
    source_dir: str,
    dest_dir: str,
    files: list[str],
    progress: bool = True,
):
    """
    Move files using os.replace.

    :param source_dir: Source directory
    :param dest_dir: Source directory
    :param files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param progress: Show progress bar.
    """

    for file in tqdm.tqdm(files, disable=not progress):
        os.replace(os.path.join(source_dir, file), os.path.join(dest_dir, file))


def copy(
    source_dir: str,
    dest_dir: str,
    files: list[str],
    progress: bool = True,
):
    """
    Copy files using shutil.copy2.

    :param source_dir: Source directory
    :param dest_dir: Source directory
    :param files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param progress: Show progress bar.
    """

    for file in tqdm.tqdm(files, disable=not progress):
        shutil.copy2(os.path.join(source_dir, file), os.path.join(dest_dir, file))


def diff(
    source_dir: str,
    dest_dir: str,
    files: list[str],
) -> dict[list[str]]:
    """
    Check if files exist.

    :param str source_dir: Source directory (optionally with hostname).
    :param str dest_dir: Source directory (optionally with hostname).
    :param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
    :param verbose: Verbose commands.
    :return:
        Dictionary with differences::

            {
                "?=" : [ ... ], # in source_dir and dest_dir
                "->" : [ ... ], # in source_dir not in dest_dir
                "<-" : [ ... ], # in dest_dir not in source_dir
            }
    """

    insource = np.array([os.path.exists(os.path.join(source_dir, file)) for file in files])
    indest = np.array([os.path.exists(os.path.join(dest_dir, file)) for file in files])
    files = np.array(files)

    return {
        "?=": files[np.logical_and(insource, indest)].tolist(),
        "->": files[np.logical_and(insource, ~indest)].tolist(),
        "<-": files[np.logical_and(~insource, indest)].tolist(),
    }
