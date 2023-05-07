import pathlib
import unittest

import numpy as np

import shelephant
from shelephant import shelephant_cp
from shelephant import shelephant_dump
from shelephant.detail import create_dummy_files
from shelephant.path import cwd
from shelephant.path import info
from shelephant.path import tempdir


class Test_shelephant_dump(unittest.TestCase):
    def test_checksum(self):
        with tempdir():
            files = ["foo.txt", "bar.txt"]
            check = create_dummy_files(files)
            shelephant_dump(["-i"] + files)
            data, _ = shelephant.dataset.interpret_file("shelephant_dump.yaml")
            self.assertEqual(check, data)

    def test_find(self):
        with tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            shelephant_dump(["-i", "-c", "find . -name '*.txt'"])
            data, _ = shelephant.dataset.interpret_file("shelephant_dump.yaml")
            self.assertEqual(check, data)

    def test_append(self):
        with tempdir():
            files = ["foo.pdf", "bar.pdf", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            pdf = [i for i in files if i.endswith(".pdf")]

            # plain

            shelephant_dump(pdf)
            data, _ = shelephant.dataset.interpret_file("shelephant_dump.yaml")
            self.assertEqual(list(data.keys()), pdf)

            shelephant_dump(["-a", "-c", "find . -name '*.txt'"])
            data, _ = shelephant.dataset.interpret_file("shelephant_dump.yaml")
            self.assertEqual(sorted(data.keys()), sorted(files))

            # with details

            shelephant_dump(["-f", "-i"] + pdf)
            data, _ = shelephant.dataset.interpret_file("shelephant_dump.yaml")
            self.assertEqual(sorted(pdf), sorted(data.keys()))
            for filename in data:
                self.assertEqual(check[filename], data[filename])

            shelephant_dump(["-a", "-i", "-c", "find . -name '*.txt'"])
            data, _ = shelephant.dataset.interpret_file("shelephant_dump.yaml")
            self.assertEqual(sorted(files), sorted(data.keys()))
            for filename in data:
                self.assertEqual(check[filename], data[filename])


class Test_shelephant_cp(unittest.TestCase):
    def test_basic(self):
        with tempdir():
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)
                shelephant_cp(["-f", "--quiet", "../dest"])

            with cwd("dest"):
                data = {file: info(file) for file in files}

            self.assertEqual(data, check)


if __name__ == "__main__":
    unittest.main()
