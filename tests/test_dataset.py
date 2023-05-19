import contextlib
import io
import os
import pathlib
import re
import unittest

import shelephant
from shelephant._tests import create_dummy_files
from shelephant.cli import f_dump
from shelephant.cli import shelephant_dump
from shelephant.search import cwd
from shelephant.search import tempdir

has_ssh = shelephant.ssh.has_keys_set("localhost")


def _plain(text):
    return list(filter(None, [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]))


class Test_Location(unittest.TestCase):
    def test_yaml(self):
        with tempdir():
            data = {
                "root": ".",
                "files": [
                    "foo.txt",
                    "bar.txt",
                    {"path": "a.txt", "sha256": "a", "size": 3},
                    {"path": "c.txt", "sha256": "c", "size": 10},
                    {"path": "d.txt", "sha256": "d", "size": 15},
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
            loc.dump = f_dump
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
        a._has_info = [False, True, True, False]

        b = shelephant.dataset.Location(root=".", files=["a.h5", "b.h5", "c.h5"])
        b._sha256 = ["a", "b", "none"]
        b._has_info = [True, True, True]

        check = {
            "->": ["mydir/e.h5"],
            "<-": [],
            "==": ["b.h5"],
            "?=": ["a.h5"],
            "!=": ["c.h5"],
        }

        self.assertEqual(a.diff(b), check)


class Test_dataset(unittest.TestCase):
    def test_basic(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                s1 = create_dummy_files(files)

            with cwd(source2):
                s2 = create_dummy_files(["a.txt", "b.txt"])
                s2 += create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt"])
                shelephant.dataset.remove(["source2"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt"])
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == x",
                "d.txt source1 == x",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertEqual(pathlib.Path(os.path.realpath("a.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("b.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("c.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("d.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("e.txt")).parent.name, "source2")
                self.assertEqual(pathlib.Path(os.path.realpath("f.txt")).parent.name, "source2")

            with cwd(dataset):
                self.assertRaises(AssertionError, shelephant.dataset.add, ["source2", "foo"])
                l1 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source1.yaml")
                l2 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source2.yaml")
                self.assertTrue(s1 == l1)
                self.assertTrue(s2 == l2)

                sym = shelephant.dataset.Location(root=".")
                sym.search = [{"rglob": "*.txt"}]
                sym.read().getinfo()
                self.assertTrue((s1 + s2).unique() == sym)

            # copy source1 -> source2

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.cp(["source1", "source2", "-n", "--colors", "none"] + files)
                shelephant.dataset.cp(["source1", "source2", "-f", "-q"] + files)

            expect = [
                "c.txt -> c.txt",
                "d.txt -> d.txt",
                "a.txt == a.txt",
                "b.txt == b.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == ==",
                "d.txt source1 == ==",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            # copy source2 -> source1

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                files += ["e.txt", "f.txt"]
                shelephant.dataset.cp(["source2", "source1", "-n", "--colors", "none"] + files)
                shelephant.dataset.cp(["source2", "source1", "-f", "-q"] + files)

            expect = [
                "e.txt -> e.txt",
                "f.txt -> f.txt",
                "a.txt == a.txt",
                "b.txt == b.txt",
                "c.txt == c.txt",
                "d.txt == d.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == ==",
                "d.txt source1 == ==",
                "e.txt source1 == ==",
                "f.txt source1 == ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertEqual(pathlib.Path(os.path.realpath("a.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("b.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("c.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("d.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("e.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("f.txt")).parent.name, "source1")

            for s in [source1, source2]:
                with cwd(s):
                    f = shelephant.dataset.Location(root=".")
                    f.search = [{"rglob": "*.txt"}]
                    f.read().getinfo()
                    self.assertTrue((s1 + s2).unique() == f)

    def test_basic_ssh(self):
        """
        shelephant_cp <sourceinfo.yaml> <dest_dirname_on_host> --ssh <user@host>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as source2:
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")

            dataset.mkdir()
            source1.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                s1 = create_dummy_files(files)

            with cwd(source2):
                s2 = create_dummy_files(["a.txt", "b.txt"])
                s2 += create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt"])
                shelephant.dataset.add(
                    ["source2", str(source2), "--ssh", "localhost", "--rglob", "*.txt"]
                )
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == x",
                "d.txt source1 == x",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertEqual(pathlib.Path(os.path.realpath("a.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("b.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("c.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("d.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("e.txt")).parent.name, "dead-link")
                self.assertEqual(pathlib.Path(os.path.realpath("f.txt")).parent.name, "dead-link")

            with cwd(dataset):
                self.assertRaises(AssertionError, shelephant.dataset.add, ["source2", "foo"])
                l1 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source1.yaml")
                l2 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source2.yaml")
                self.assertTrue(s1 == l1)
                self.assertTrue(s2 == l2)

                sym = shelephant.dataset.Location(root=".")
                sym.search = [{"rglob": "*.txt"}]
                self.assertTrue((s1 + s2).unique().files(False) == sym.read().sort().files(False))

            # copy source1 -> source2

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.cp(["source1", "source2", "-n", "--colors", "none"] + files)
                shelephant.dataset.cp(["source1", "source2", "-f", "-q"] + files)

            expect = [
                "c.txt -> c.txt",
                "d.txt -> d.txt",
                "a.txt == a.txt",
                "b.txt == b.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == ==",
                "d.txt source1 == ==",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            # copy source2 -> source1

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                files += ["e.txt", "f.txt"]
                shelephant.dataset.cp(["source2", "source1", "-n", "--colors", "none"] + files)
                shelephant.dataset.cp(["source2", "source1", "-f", "-q"] + files)

            expect = [
                "e.txt -> e.txt",
                "f.txt -> f.txt",
                "a.txt == a.txt",
                "b.txt == b.txt",
                "c.txt == c.txt",
                "d.txt == d.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == ==",
                "d.txt source1 == ==",
                "e.txt source1 == ==",
                "f.txt source1 == ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertEqual(pathlib.Path(os.path.realpath("a.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("b.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("c.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("d.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("e.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("f.txt")).parent.name, "source1")

            for s in [source1, source2]:
                with cwd(s):
                    f = shelephant.dataset.Location(root=".")
                    f.search = [{"rglob": "*.txt"}]
                    f.read().getinfo()
                    self.assertTrue((s1 + s2).unique() == f)

    def test_shallow(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")
            source3 = pathlib.Path("source3")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()
            source3.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(source3):
                create_dummy_files(["g.txt"], slice(8, None, None))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt"])
                shelephant.dataset.add(["source3", "../source3", "--rglob", "*.txt", "--shallow"])
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == == x",
                "b.txt source1 == == x",
                "c.txt source1 == x x",
                "d.txt source1 == x x",
                "e.txt source2 x == x",
                "f.txt source2 x == x",
                "g.txt source3 x x ?=",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertEqual(pathlib.Path(os.path.realpath("a.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("b.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("c.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("d.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("e.txt")).parent.name, "source2")
                self.assertEqual(pathlib.Path(os.path.realpath("f.txt")).parent.name, "source2")
                self.assertEqual(pathlib.Path(os.path.realpath("g.txt")).parent.name, "source3")

    def test_unavailable(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")
            source3 = pathlib.Path("source3")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()
            source3.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(source3):
                create_dummy_files(["g.txt"], slice(8, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt"])
                shelephant.dataset.add(["source3", "../source3", "--rglob", "*.txt", "--shallow"])

            os.rename("source3", "foo")
            with cwd(dataset):
                shelephant.dataset.update([])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == == x",
                "b.txt source1 == == x",
                "c.txt source1 == x x",
                "d.txt source1 == x x",
                "e.txt source2 x == x",
                "f.txt source2 x == x",
                "g.txt ---- x x ?=",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertEqual(pathlib.Path(os.path.realpath("a.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("b.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("c.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("d.txt")).parent.name, "source1")
                self.assertEqual(pathlib.Path(os.path.realpath("e.txt")).parent.name, "source2")
                self.assertEqual(pathlib.Path(os.path.realpath("f.txt")).parent.name, "source2")
                self.assertIn(
                    pathlib.Path(os.path.realpath("g.txt")).parent.name,
                    ["unavailable", "dead-link"],
                )


if __name__ == "__main__":
    unittest.main()
