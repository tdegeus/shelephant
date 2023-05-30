import os
import pathlib

if __name__ == "__main__":
    if pathlib.Path("remove.txt").exists():
        for file in pathlib.Path("remove.txt").read_text().splitlines():
            os.remove(file)
