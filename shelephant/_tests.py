"""
Not part of public API.
"""
import os
import pathlib

import numpy as np

from . import dataset


def create_dummy_files(filenames: list[str], keep: list = None) -> dataset.Location:
    """
    Create dummy files in the current directory.

    :param filenames: List of filenames.
    :param keep: Select a subset of available dummy files.
        For example ``keep=[0, -1]`` or ``keep=slice(0, None, 2)``.

    :return: dataset.Location
    """

    content = {
        "foo": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        "bar": "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        "a": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
        "b": "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
        "c": "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6",
        "d": "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",
        "e": "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca046dea",
        "f": "252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111",
        "g": "cd0aa9856147b6c5b4ff2b7dfee5da20aa38253099ef1b4a64aced233c9afe29",
    }

    if keep is not None:
        keys = list(content.keys())
        keep = np.arange(len(keys))[keep]
        content = {keys[i]: content[keys[i]] for i in keep}

    assert len(filenames) <= len(content)

    ret = {}
    for file, (content, sha) in zip(filenames, content.items()):
        pathlib.Path(file).write_text(content)
        ret[file] = {
            "sha256": sha,
            "size": os.path.getsize(file),
            "mtime": os.path.getmtime(file),
        }

    return dataset.Location(root=".", files=ret)
