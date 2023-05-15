import os
import pathlib
import unittest

import shelephant
from shelephant import shelephant_dump
from shelephant._tests import create_dummy_files
from shelephant.search import tempdir

has_ssh = shelephant.ssh.has_keys_set("localhost")


class Test_Location(unittest.TestCase):
    def test_yaml(self):
        with tempdir():
            data = {
                "root": ".",
                "files": [
                    "foo.txt",
                    "bar.txt",
                    {"path": "a.txt", "sha256": "a"},
                    {"path": "c.txt", "sha256": "c", "size": 10},
                    {"path": "d.txt", "size": 15},
                ],
            }
            shelephant.yaml.dump("foo.yaml", data)
            loc = shelephant.dataset.Location.from_yaml("foo.yaml")
            self.assertEqual(loc.asdict(), data)

            loc.to_yaml("bar.yaml")
            self.assertEqual(
                pathlib.Path("foo.yaml").read_text(), pathlib.Path("bar.yaml").read_text()
            )

    def test_info(self):
        with tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            loc = shelephant.dataset.Location(root=".", files=files).getinfo()
            self.assertTrue(check == loc)

    def test_info_ssh(self):
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with shelephant.ssh.tempdir("localhost") as remote, tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            shelephant.scp.copy(".", f'localhost:"{str(remote)}"', files, progress=False)
            [os.remove(f) for f in files]
            loc = shelephant.dataset.Location(root=remote, ssh="localhost", files=files)
            loc.python = "python3"
            loc.getinfo()
            self.assertTrue(check == loc)

    def test_read_dump(self):
        with tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            shelephant_dump(files)

            loc = shelephant.dataset.Location(root=".")
            loc.dump = shelephant.f_dump
            loc.read().getinfo()
            self.assertTrue(check == loc)

    def test_search(self):
        with tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)

            loc = shelephant.dataset.Location(root=".")
            loc.search = [{"rglob": "*.txt"}]
            loc.read().getinfo()
            self.assertTrue(check == loc)

    def test_search_ssh(self):
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with shelephant.ssh.tempdir("localhost") as remote, tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            shelephant.scp.copy(".", f'localhost:"{str(remote)}"', files, progress=False)

            loc = shelephant.dataset.Location(root=remote, ssh="localhost")
            loc.python = "python3"
            loc.search = [{"rglob": "*.txt"}]
            loc.read().getinfo()
            self.assertTrue(check == loc)

    def test_diff(self):
        a = shelephant.dataset.Location(root=".", files=["a.h5", "b.h5", "c.h5", "mydir/e.h5"])
        a._sha256 = [None, "b", "c", None]
        a._has_sha256 = [False, True, True, False]

        b = shelephant.dataset.Location(root=".", files=["a.h5", "b.h5", "c.h5"])
        b._sha256 = ["a", "b", "none"]
        b._has_sha256 = [True, True, True]

        check = {
            "->": ["mydir/e.h5"],
            "<-": [],
            "==": ["b.h5"],
            "?=": ["a.h5"],
            "!=": ["c.h5"],
        }

        self.assertEqual(a.diff(b), check)


if __name__ == "__main__":
    unittest.main()
