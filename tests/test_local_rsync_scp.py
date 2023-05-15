import pathlib
import shutil
import unittest

import shelephant
from shelephant._tests import create_dummy_files
from shelephant.search import cwd
from shelephant.search import tempdir

has_rsync = shutil.which("rsync") is not None


class Test_local(unittest.TestCase):
    def test_diff(self):
        with tempdir():
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                create_dummy_files(files)
                data = shelephant.local.diff(".", "../dest", files)

            check = {
                "?=": ["foo.txt", "bar.txt"],
                "->": ["more.txt", "even_more.txt"],
                "<-": [],
            }
            self.assertEqual(data, check)

    def test_copy(self):
        with tempdir():
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant.local.copy(".", "../dest", files, progress=False)

            with cwd("dest"):
                data = shelephant.dataset.Location(root=".", files=files).getinfo()

            self.assertTrue(check == data)


class Test_scp(unittest.TestCase):
    def test_copy(self):
        with tempdir():
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant.scp.copy(".", "../dest", files, progress=False)

            with cwd("dest"):
                data = shelephant.dataset.Location(root=".", files=files).getinfo()

            self.assertTrue(check == data)


class Test_rsync(unittest.TestCase):
    def test_diff(self):
        if not has_rsync:
            self.skipTest("rsync not found")

        with tempdir():
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                create_dummy_files(files)
                data = shelephant.rsync.diff(".", "../dest", files)

            check = {
                "==": ["foo.txt"],
                "!=": ["bar.txt"],
                "->": ["more.txt", "even_more.txt"],
            }
            self.assertEqual(data, check)

    def test_copy(self):
        if not has_rsync:
            self.skipTest("rsync not found")

        with tempdir():
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant.rsync.copy(".", "../dest", files, progress=False)

            with cwd("dest"):
                data = shelephant.dataset.Location(root=".", files=files).getinfo()

            self.assertTrue(check == data)


if __name__ == "__main__":
    unittest.main()
