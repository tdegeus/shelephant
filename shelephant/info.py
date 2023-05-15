import hashlib
import os
import pathlib
import sys

try:
    from tqdm import tqdm
except ImportError:

    def tqdm(iterator, *args, **kwargs):
        return iterator


def getinfo(files: list[pathlib.Path], progress: bool = True) -> tuple[list[str], list[int]]:
    """
    Get the sha256 hash and size of a list of files.

    :param files: A list of files.
    :param progress: Show a progress bar.
    :return: A tuple of lists of hashes and sizes.
    """

    ret_hash = []
    ret_size = []

    if sys.version_info >= (3, 11):
        for filename in tqdm(files, disable=not progress):
            ret_size.append(os.path.getsize(filename))
            with open(filename, "rb", buffering=0) as f:
                ret_hash.append(hashlib.file_digest(f, "sha256").hexdigest())

    else:
        for filename in tqdm(files, disable=not progress):
            ret_size.append(os.path.getsize(filename))
            h = hashlib.sha256()
            b = bytearray(128 * 1024)
            mv = memoryview(b)
            with open(filename, "rb", buffering=0) as f:
                while n := f.readinto(mv):
                    h.update(mv[:n])
            ret_hash.append(h.hexdigest())

    return ret_hash, ret_size


if __name__ == "__main__":
    hash, size = getinfo(pathlib.Path("files.txt").read_text().splitlines())
    pathlib.Path("sha256.txt").write_text("\n".join(hash))
    pathlib.Path("size.txt").write_text("\n".join(map(str, size)))
