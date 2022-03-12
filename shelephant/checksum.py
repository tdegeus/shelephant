r"""
Compute checksums.

(c) Tom de Geus, 2021, MIT
"""
import os

import numpy as np
import tqdm

from .relpath import add_prefix
from .yaml import read


def sha256(filename, size=2**10):
    r"""
    Get sha256 of a file.
    """

    import hashlib

    h = hashlib.sha256()

    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(size * h.block_size), b""):
            h.update(byte_block)
        return h.hexdigest()


def get(filepaths, yaml_hostinfo=None, hybrid=False, progress=False):
    r"""
    Compute the checksums of a list of files.

    :param list filepaths: List of file-paths.

    :param set yaml_hostinfo:
        File-path of a host-info file (see :py:mod:`shelephant.cli.hostinfo`).
        If specified the checksums are **not** computed, but exclusively read from the
        host-file. The user is responsible for keeping them up-to-date.

    :param bool hybrid:
        If ``True``, the function first tries to read from ``yaml_hostinfo``, and then
        computes missing items on the fly.

    :param bool progress: Show a progress-bar.

    :return:
        List of checksums, of same length as ``filepaths``.
        The entry is ``None`` if no checksum was found/read.
    """

    if type(filepaths) == str:
        filepaths = [filepaths]

    n = len(filepaths)
    ret = [None for i in range(n)]

    # Compute

    if not yaml_hostinfo:

        for i in tqdm.trange(n, disable=not progress, desc="Processing"):
            if os.path.isfile(filepaths[i]):
                ret[i] = sha256(filepaths[i])

        return ret

    # Read pre-computed

    data = read(yaml_hostinfo)
    files = data["files"]
    prefix = data["prefix"]
    check_sums = data["checksum"]
    check_paths = add_prefix(prefix, files)

    sorter = np.argsort(filepaths)
    source_paths = np.array(filepaths)[sorter]

    i = np.argsort(check_paths)
    check_paths = np.array(check_paths)[i]
    check_sums = np.array(check_sums)[i]

    test = np.in1d(source_paths, check_paths)
    idx = np.searchsorted(check_paths, source_paths)
    idx = np.where(test, idx, 0)
    ret = np.where(test, check_sums[idx], None)
    out = np.empty_like(ret)
    out[sorter] = ret
    ret = list(out)

    if hybrid:
        for i in tqdm.trange(n, disable=not progress, desc="Processing"):
            if ret[i] is None:
                if os.path.isfile(filepaths[i]):
                    ret[i] = sha256(filepaths[i])

    return ret
