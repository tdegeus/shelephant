import hashlib
import os
import pathlib
import sys

try:
    from tqdm import tqdm
except ImportError:

    def tqdm(iterator, *args, **kwargs):
        return iterator


def compute_sha256(
    files: list[pathlib.Path], sha256: bool = True, progress: bool = True
) -> tuple[list[str], list[int]]:
    """
    Get the sha256 hash and size of a list of files.

    :param files: A list of files.
    :param sha256: Calculate the sha256 hash.
    :param progress: Show a progress bar.
    :return: A tuple of lists of (size, mtime, sha256).
    """

    ret_hash = []
    ret_size = []
    ret_mtime = []

    if not sha256:
        for filename in tqdm(files, disable=not progress):
            if not os.path.exists(filename):
                ret_size.append(-1)
                ret_mtime.append(-1)
                ret_hash.append("")
                continue
            ret_size.append(os.path.getsize(filename))
            ret_mtime.append(os.path.getmtime(filename))

    elif sys.version_info >= (3, 11):
        for filename in tqdm(files, disable=not progress):
            if not os.path.exists(filename):
                ret_size.append(-1)
                ret_mtime.append(-1)
                ret_hash.append("")
                continue
            ret_size.append(os.path.getsize(filename))
            ret_mtime.append(os.path.getmtime(filename))
            with open(filename, "rb", buffering=0) as f:
                ret_hash.append(hashlib.file_digest(f, "sha256").hexdigest())

    else:
        for filename in tqdm(files, disable=not progress):
            if not os.path.exists(filename):
                ret_size.append(-1)
                ret_mtime.append(-1)
                ret_hash.append("")
                continue
            ret_size.append(os.path.getsize(filename))
            ret_mtime.append(os.path.getmtime(filename))
            h = hashlib.sha256()
            b = bytearray(128 * 1024)
            mv = memoryview(b)
            with open(filename, "rb", buffering=0) as f:
                while n := f.readinto(mv):
                    h.update(mv[:n])
            ret_hash.append(h.hexdigest())

    return ret_size, ret_mtime, ret_hash


if __name__ == "__main__":
    sha256 = pathlib.Path("sha256.txt").exists()
    size, mtime, csum = compute_sha256(
        pathlib.Path("files.txt").read_text().splitlines(), sha256=sha256
    )
    pathlib.Path("size.txt").write_text("\n".join(map(str, size)))
    pathlib.Path("mtime.txt").write_text("\n".join(map(str, mtime)))
    pathlib.Path("sha256.txt").write_text("\n".join(csum))
