import hashlib
import os
import pathlib
import sys

ret_hash = []
ret_size = []
files = pathlib.Path("files.txt").read_text().splitlines()

if sys.version_info >= (3, 11):
    for filename in files:
        ret_size.append(os.path.getsize(filename))
        with open(filename, "rb", buffering=0) as f:
            ret_hash.append(hashlib.file_digest(f, "sha256").hexdigest())

else:
    for filename in files:
        ret_size.append(os.path.getsize(filename))
        h = hashlib.sha256()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        with open(filename, "rb", buffering=0) as f:
            while n := f.readinto(mv):
                h.update(mv[:n])
        ret_hash.append(h.hexdigest())


pathlib.Path("sha256.txt").write_text("\n".join(ret_hash))
pathlib.Path("size.txt").write_text("\n".join(map(str, ret_size)))
