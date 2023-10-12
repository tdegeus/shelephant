import contextlib
import io
import os
import pathlib
import re
import unittest

import numpy as np

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
                    {"path": "a.txt", "sha256": "a", "size": 3, "mtime": 0.0},
                    {"path": "c.txt", "sha256": "c", "size": 10, "mtime": 0.0},
                    {"path": "d.txt", "sha256": "d", "size": 15, "mtime": 0.0},
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
    def test_pwd(self):
        with tempdir():
            base = pathlib.Path.cwd()
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")

            dataset.mkdir()
            source1.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.pwd(["source1", "--abs"])
            self.assertEqual(sio.getvalue().strip(), str((base / "source1").absolute()))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.pwd(["source1"])
            self.assertEqual(sio.getvalue().strip(), os.path.join("..", "source1"))

    def test_status_partial(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")

            dataset.mkdir()
            source1.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                source = create_dummy_files(files)

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])

            with cwd(dataset):
                links = shelephant.dataset.Location(root=".")
                links.search = [{"rglob": "*.txt"}]
                links.read().getinfo()
                self.assertTrue(source == links)

            with cwd(source1):
                pathlib.Path("b.txt").write_text("foo-foo")
                pathlib.Path("d.txt").write_text("foo-bar")
                source = shelephant.dataset.Location(root=".")
                source.search = [{"rglob": "*.txt"}]
                source.read().getinfo()

            with cwd(dataset):
                shelephant.dataset.update(["source1", "d.txt", "b.txt", "-q"])
                data = shelephant.dataset.Location.from_yaml(".shelephant/storage/source1.yaml")
                self.assertTrue(source == data)

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

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])
                shelephant.dataset.remove(["source2"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
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
                for f in ["a.txt", "b.txt", "c.txt", "d.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")
                for f in ["e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source2")

            with cwd(dataset):
                self.assertRaises(AssertionError, shelephant.dataset.add, ["source2", "foo"])
                l1 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source1.yaml")
                l2 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source2.yaml")
                self.assertTrue(s1 == l1)
                self.assertTrue(s2 == l2)

                sym = shelephant.dataset.Location(root=".")
                sym.search = [{"rglob": "*.txt"}]
                sym.read().getinfo()
                self.assertTrue(s1 + s2 == sym)

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
                for f in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")

            for s in [source1, source2]:
                with cwd(s):
                    f = shelephant.dataset.Location(root=".")
                    f.search = [{"rglob": "*.txt"}]
                    f.read().getinfo()
                    self.assertTrue(s1 + s2 == f)

    def test_basic_ssh(self):
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

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    ["source2", str(source2), "--ssh", "localhost", "--rglob", "*.txt", "-q"]
                )

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
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
                for f in ["b.txt", "b.txt", "c.txt", "d.txt"]:
                    self.assertEqual(pathlib.Path(os.path.realpath(f)).parent.name, "source1")
                for f in ["e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(os.path.realpath(f)).parent.name, "dead-link")

            with cwd(dataset):
                self.assertRaises(AssertionError, shelephant.dataset.add, ["source2", "foo", "-q"])
                l1 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source1.yaml")
                l2 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source2.yaml")
                self.assertTrue(s1 == l1)
                self.assertTrue(s2 == l2)

                sym = shelephant.dataset.Location(root=".")
                sym.search = [{"rglob": "*.txt"}]
                self.assertTrue((s1 + s2).files(False) == sym.read().sort().files(False))

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
                for f in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")

            for s in [source1, source2]:
                with cwd(s):
                    f = shelephant.dataset.Location(root=".")
                    f.search = [{"rglob": "*.txt"}]
                    f.read().getinfo()
                    self.assertTrue(s1 + s2 == f)

    def test_basic_ssh_mount(self):
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as source2:
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            mount = pathlib.Path("mount")

            dataset.mkdir()
            source1.mkdir()
            mount.symlink_to(source2)

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                s1 = create_dummy_files(files)

            with cwd(source2):
                s2 = create_dummy_files(["a.txt", "b.txt"])
                s2 += create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    [
                        "source2",
                        str(source2),
                        "--ssh",
                        "localhost",
                        "--mount",
                        str(mount),
                        "--rglob",
                        "*.txt",
                        "-q",
                    ]
                )

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
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
                for f in ["a.txt", "b.txt", "c.txt", "d.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")
                for f in ["e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source2")
                    self.assertEqual(pathlib.Path(os.path.realpath(f)).parent.name, "mount")

            with cwd(dataset):
                self.assertRaises(AssertionError, shelephant.dataset.add, ["source2", "foo", "-q"])
                l1 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source1.yaml")
                l2 = shelephant.dataset.Location.from_yaml(".shelephant/storage/source2.yaml")
                self.assertTrue(s1 == l1)
                self.assertTrue(s2 == l2)

                sym = shelephant.dataset.Location(root=".")
                sym.search = [{"rglob": "*.txt"}]
                self.assertTrue((s1 + s2).files(False) == sym.read().sort().files(False))

    def test_basic_manual(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.yaml.dump(
                    ".shelephant/storage/source1.yaml",
                    {"root": "../../../source1", "search": [{"rglob": "*.txt"}]},
                )
                shelephant.yaml.dump(
                    ".shelephant/storage/source2.yaml",
                    {"root": "../../../source2", "search": [{"rglob": "*.txt"}]},
                )
                f = ".shelephant/storage.yaml"
                shelephant.dataset.update(["--base-link", "source1", "-q"])
                shelephant.dataset.update(["--base-link", "source2", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
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
                for f in ["a.txt", "b.txt", "c.txt", "d.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")
                for f in ["e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source2")

    def test_cp(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            (source1 / "mydir").mkdir()
            source2.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt"])
                with cwd("mydir"):
                    create_dummy_files(["c.txt", "d.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset / "mydir"):
                shelephant.dataset.cp(["source1", "source2", "c.txt", "-f", "-q"])

            self.assertTrue((source1 / "mydir" / "c.txt").exists())

    def test_cp_clone(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt", "c.txt", "d.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset):
                shelephant.dataset.cp(["source1", "source2", ".", "-f", "-q"])

            self.assertTrue((source2 / "a.txt").exists())
            self.assertTrue((source2 / "b.txt").exists())
            self.assertTrue((source2 / "c.txt").exists())
            self.assertTrue((source2 / "d.txt").exists())

    def test_mv(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt", "c.txt", "d.txt"])

            with cwd(source2):
                create_dummy_files(["e.txt", "f.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == x",
                "b.txt source1 == x",
                "c.txt source1 == x",
                "d.txt source1 == x",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                files = ["c.txt", "d.txt"]
                shelephant.dataset.mv(["source1", "source2", "-n", "--colors", "none"] + files)
                shelephant.dataset.mv(["source1", "source2", "-f", "-q"] + files)

            expect = [
                "c.txt -> c.txt",
                "d.txt -> d.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == x",
                "b.txt source1 == x",
                "c.txt source2 x ==",
                "d.txt source2 x ==",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_mv_here(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt"])

            with cwd(dataset):
                create_dummy_files(["c.txt", "d.txt"])

            with cwd(source2):
                create_dummy_files(["e.txt", "f.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])
                data = shelephant.yaml.read(".shelephant/storage/here.yaml")
                data["search"] = [{"rglob": "*.txt"}]
                shelephant.yaml.dump(".shelephant/storage/here.yaml", data, force=True)
                shelephant.dataset.update(["-q", "here"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == x",
                "b.txt source1 == x",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
                "c.txt here ? ?",
                "d.txt here ? ?",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                files = ["c.txt", "d.txt"]
                shelephant.dataset.mv(["here", "source2", "-n", "--colors", "none"] + files)
                shelephant.dataset.mv(["here", "source2", "-f", "-q"] + files)

            expect = [
                "c.txt -> c.txt",
                "d.txt -> d.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == x",
                "b.txt source1 == x",
                "c.txt source2 x ==",
                "d.txt source2 x ==",
                "e.txt source2 x ==",
                "f.txt source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_rm(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")

            dataset.mkdir()
            source1.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])

            with cwd(dataset):
                shelephant.dataset.rm(["source1", "a.txt", "-f", "-q"])

            self.assertFalse((source1 / "a.txt").exists())

    def test_unmanage(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")

            dataset.mkdir()
            source1.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])

            with cwd(dataset):
                create_dummy_files(["c.txt"], slice(2, None, None))

            with cwd(source1):
                create_dummy_files(["c.txt"], slice(3, None, None))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.update(["source1", "--quiet"])

            expect = [
                "Local files conflicting with dataset. No links are created for these files:",
                "c.txt",
            ]
            ret = _plain(sio.getvalue())
            self.assertEqual(ret, expect)

            with cwd(dataset):
                self.assertFalse(pathlib.Path("c.txt").is_symlink())

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

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    ["source3", "../source3", "--rglob", "*.txt", "--shallow", "-q"]
                )

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == == x",
                "b.txt source1 == == x",
                "c.txt source1 == x x",
                "d.txt source1 == x x",
                "e.txt source2 x == x",
                "f.txt source2 x == x",
                "g.txt source3 x x ?",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                for f in ["a.txt", "b.txt", "c.txt", "d.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")
                for f in ["e.txt", "f.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source2")
                for f in ["g.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source3")

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
                files = ["b.txt", "c.txt", "d.txt", "h.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["b.txt"])
                create_dummy_files(["c.txt"], slice(3, None, None))
                create_dummy_files(["e.txt", "k.txt"], slice(4, None, None))

            with cwd(source3):
                info = create_dummy_files(["b.txt"])
                create_dummy_files(["a.txt", "g.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    ["source3", "../source3", "--rglob", "*.txt", "--shallow", "-q"]
                )
                loc = shelephant.dataset.Location.from_yaml(".shelephant/storage/source3.yaml")
                i = np.argwhere(loc._files == "b.txt").ravel()[0]
                loc._has_info[i] = True
                loc._sha256[i] = info._sha256[0]
                loc._mtime[i] = info._mtime[0]
                loc._size[i] = info._size[0]
                loc.to_yaml(".shelephant/storage/source3.yaml", force=True)

            os.rename("source3", "foo")
            with cwd(dataset):
                shelephant.dataset.update(["--quiet"])

            # make test robust against filesystems with low mtime resolution
            with cwd(dataset / ".shelephant" / "storage"):
                loc = shelephant.dataset.Location.from_yaml("source1.yaml")
                loc._mtime[np.argwhere(np.equal(loc._files, "c.txt")).ravel()[0]] = 3
                loc.to_yaml("source1.yaml", force=True)

                loc = shelephant.dataset.Location.from_yaml("source2.yaml")
                loc._mtime[np.argwhere(np.equal(loc._files, "c.txt")).ravel()[0]] = 1
                loc.to_yaml("source2.yaml", force=True)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt ---- x x ?",
                "b.txt source1 == == ==",
                "c.txt source1 2 1 x",
                "d.txt source1 == x x",
                "e.txt source2 x == x",
                "g.txt ---- x x ?",
                "h.txt source1 == x x",
                "k.txt source2 x == x",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                for f in ["b.txt", "c.txt", "d.txt", "h.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source1")
                for f in ["e.txt", "k.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source2")
                for f in ["a.txt", "g.txt"]:
                    self.assertEqual(pathlib.Path(f).readlink().parent.name, "source3")

    def test_prefix(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1/foo")
            source2 = pathlib.Path("source2/foo")
            source3 = pathlib.Path("source3")

            dataset.mkdir()
            source1.mkdir(parents=True)
            source2.mkdir(parents=True)
            source3.mkdir()

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(source3):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    ["source3", "../source3", "--rglob", "*.txt", "--prefix", "foo", "-q"]
                )

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                os.path.join("foo", "a.txt") + " source1 == == ==",
                os.path.join("foo", "b.txt") + " source1 == == ==",
                os.path.join("foo", "c.txt") + " source1 == x ==",
                os.path.join("foo", "d.txt") + " source1 == x ==",
                os.path.join("foo", "e.txt") + " source2 x == x",
                os.path.join("foo", "f.txt") + " source2 x == x",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset / "foo"):
                self.assertEqual(
                    pathlib.Path(os.path.realpath("a.txt")).parent.parent.name, "source1"
                )
                self.assertEqual(
                    pathlib.Path(os.path.realpath("b.txt")).parent.parent.name, "source1"
                )
                self.assertEqual(
                    pathlib.Path(os.path.realpath("c.txt")).parent.parent.name, "source1"
                )
                self.assertEqual(
                    pathlib.Path(os.path.realpath("d.txt")).parent.parent.name, "source1"
                )
                self.assertEqual(
                    pathlib.Path(os.path.realpath("e.txt")).parent.parent.name, "source2"
                )
                self.assertEqual(
                    pathlib.Path(os.path.realpath("f.txt")).parent.parent.name, "source2"
                )

    def test_hidden(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                files = [".a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files([".a.txt", "b.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                ".a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == x",
                "d.txt source1 == x",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_lock(self):
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

            path = os.path.join(".shelephant", "storage", "source2.yaml")
            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    [
                        "source2",
                        "../source2",
                        "--rglob",
                        "*.txt",
                        "--skip",
                        r"[\.]?(shelephant)(.*)",
                        "-q",
                    ]
                )
                shelephant.dataset.cp(["-ex", "-fq", "here", "source2", path])

            with cwd(source2):
                s2 += create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))
                shelephant.dataset.lock(["source2"])
                shelephant.dataset.update(["--quiet"])

            with cwd(dataset):
                path = os.path.join(".shelephant", "storage", "source2.yaml")
                shelephant.dataset.cp(["-ex", "-fq", "source2", "here", path])
                shelephant.dataset.update(["--quiet"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
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
                sym = shelephant.dataset.Location(root=".")
                sym.search = [{"rglob": "*.txt"}]
                sym.read().getinfo()
                self.assertTrue(s1 + s2 == sym)

    def test_remove_empty(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                d1 = pathlib.Path("mydir")
                d1.mkdir(parents=True, exist_ok=True)
                create_dummy_files(["a.txt", "b.txt"])
                with cwd(d1):
                    create_dummy_files(["c.txt", "d.txt"], slice(2, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.rm(["source1", "mydir/c.txt", "mydir/d.txt", "-q", "-f"])
                self.assertFalse(d1.exists())

    def test_status(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                d1 = pathlib.Path("mydir")
                d2 = d1 / "foo"
                d2.mkdir(parents=True, exist_ok=True)
                create_dummy_files(["a.txt", "b.txt"])
                with cwd(d1):
                    create_dummy_files(["c.txt", "d.txt"], slice(2, None, None))
                with cwd(d2):
                    create_dummy_files(["e.txt", "f.txt"], slice(4, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])

            with cwd(dataset / "mydir"), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status([".", "--table", "PLAIN_COLUMNS"])

            expect = [
                "c.txt source1 ==",
                "d.txt source1 ==",
                os.path.join("foo", "e.txt") + " source1 ==",
                os.path.join("foo", "f.txt") + " source1 ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_status_duplicates(self):
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
                create_dummy_files(["a.txt", "b.txt", "c.txt", "d.txt"])

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["c.txt", "d.txt"], slice(4, None, None))

            with cwd(source3):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["c.txt"], slice(4, None, None))
                create_dummy_files(["d.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source3", "../source3", "--rglob", "*.txt", "-q"])

            # make test robust against filesystems with low mtime resolution
            with cwd(dataset / ".shelephant" / "storage"):
                loc = shelephant.dataset.Location.from_yaml("source1.yaml")
                loc._mtime[np.argwhere(np.equal(loc._files, "c.txt")).ravel()[0]] = 3
                loc._mtime[np.argwhere(np.equal(loc._files, "d.txt")).ravel()[0]] = 3
                loc.to_yaml("source1.yaml", force=True)

                loc = shelephant.dataset.Location.from_yaml("source2.yaml")
                loc._mtime[np.argwhere(np.equal(loc._files, "c.txt")).ravel()[0]] = 2
                loc._mtime[np.argwhere(np.equal(loc._files, "d.txt")).ravel()[0]] = 2
                loc.to_yaml("source2.yaml", force=True)

                loc = shelephant.dataset.Location.from_yaml("source3.yaml")
                loc._mtime[np.argwhere(np.equal(loc._files, "c.txt")).ravel()[0]] = 1
                loc._mtime[np.argwhere(np.equal(loc._files, "d.txt")).ravel()[0]] = 1
                loc.to_yaml("source3.yaml", force=True)

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == == ==",
                "b.txt source1 == == ==",
                "c.txt source1 2 1 1",
                "d.txt source1 3 2 1",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_gitignore(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")

            dataset.mkdir()
            source1.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt"])

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])

            with cwd(dataset):
                shelephant.dataset.gitignore([])
                shelephant.dataset.gitignore([])
                shelephant.dataset.gitignore([])
                text = pathlib.Path(".gitignore").read_text().splitlines()

            expect = [
                "# <shelephant>",
                "a.txt",
                "b.txt",
                "# </shelephant>",
            ]

            self.assertEqual(text, expect)

            with cwd(dataset):
                pathlib.Path(".gitignore").write_text("__pycache__")
                shelephant.dataset.gitignore([])
                shelephant.dataset.gitignore([])
                shelephant.dataset.gitignore([])
                text = pathlib.Path(".gitignore").read_text().splitlines()

            expect = [
                "__pycache__",
                "",
                "# <shelephant>",
                "a.txt",
                "b.txt",
                "# </shelephant>",
            ]

            self.assertEqual(text, expect)

    def test_status_on(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir()
            source2.mkdir()

            with cwd(source1):
                create_dummy_files(["a.txt", "b.txt", "c.txt", "d.txt"])

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(4, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS", "--on", "source1"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
                "c.txt source1 == x",
                "d.txt source1 == x",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_removed(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")

            dataset.mkdir()
            source1.mkdir(parents=True)
            source2.mkdir(parents=True)

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
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

            with cwd(source1):
                os.remove("c.txt")
                os.remove("d.txt")

            with cwd(source2):
                os.remove("e.txt")
                os.remove("f.txt")

            with cwd(dataset):
                shelephant.dataset.update(["all"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                "a.txt source1 == ==",
                "b.txt source1 == ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_prefix_cp_source(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")
            prefix = pathlib.Path("prefix")

            dataset.mkdir()
            source1.mkdir(parents=True)
            source2.mkdir(parents=True)

            with cwd(source1):
                files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                create_dummy_files(files)

            with cwd(source2):
                prefix.mkdir()
                with cwd(prefix):
                    create_dummy_files(["a.txt", "b.txt"])
                    create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(
                    ["source1", "../source1", "--prefix", str(prefix), "--rglob", "*.txt", "-q"]
                )
                shelephant.dataset.add(["source2", "../source2", "--rglob", "*.txt", "-q"])

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / "a.txt") + " source1 == ==",
                str(prefix / "b.txt") + " source1 == ==",
                str(prefix / "c.txt") + " source1 == x",
                str(prefix / "d.txt") + " source1 == x",
                str(prefix / "e.txt") + " source2 x ==",
                str(prefix / "f.txt") + " source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                shelephant.dataset.cp(
                    [
                        "source1",
                        "source2",
                        str(prefix / "c.txt"),
                        str(prefix / "d.txt"),
                        "-q",
                        "--force",
                    ]
                )

            with cwd(source2):
                self.assertTrue(os.path.isfile(prefix / "c.txt"))
                self.assertTrue(os.path.isfile(prefix / "d.txt"))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / "a.txt") + " source1 == ==",
                str(prefix / "b.txt") + " source1 == ==",
                str(prefix / "c.txt") + " source1 == ==",
                str(prefix / "d.txt") + " source1 == ==",
                str(prefix / "e.txt") + " source2 x ==",
                str(prefix / "f.txt") + " source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                shelephant.dataset.cp(
                    [
                        "source2",
                        "source1",
                        str(prefix / "e.txt"),
                        str(prefix / "f.txt"),
                        "-q",
                        "--force",
                    ]
                )

            with cwd(source1):
                self.assertTrue(os.path.isfile("e.txt"))
                self.assertTrue(os.path.isfile("f.txt"))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / "a.txt") + " source1 == ==",
                str(prefix / "b.txt") + " source1 == ==",
                str(prefix / "c.txt") + " source1 == ==",
                str(prefix / "d.txt") + " source1 == ==",
                str(prefix / "e.txt") + " source1 == ==",
                str(prefix / "f.txt") + " source1 == ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_prefix_cp_dest(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")
            prefix = pathlib.Path("prefix")

            dataset.mkdir()
            source1.mkdir(parents=True)
            source2.mkdir(parents=True)

            with cwd(source1):
                prefix.mkdir()
                with cwd(prefix):
                    files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                    create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(["source1", "../source1", "--rglob", "*.txt", "-q"])
                shelephant.dataset.add(
                    ["source2", "../source2", "--prefix", str(prefix), "--rglob", "*.txt", "-q"]
                )

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / "a.txt") + " source1 == ==",
                str(prefix / "b.txt") + " source1 == ==",
                str(prefix / "c.txt") + " source1 == x",
                str(prefix / "d.txt") + " source1 == x",
                str(prefix / "e.txt") + " source2 x ==",
                str(prefix / "f.txt") + " source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                shelephant.dataset.cp(
                    [
                        "source1",
                        "source2",
                        str(prefix / "c.txt"),
                        str(prefix / "d.txt"),
                        "-q",
                        "--force",
                    ]
                )

            with cwd(source2):
                self.assertTrue(os.path.isfile("c.txt"))
                self.assertTrue(os.path.isfile("d.txt"))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / "a.txt") + " source1 == ==",
                str(prefix / "b.txt") + " source1 == ==",
                str(prefix / "c.txt") + " source1 == ==",
                str(prefix / "d.txt") + " source1 == ==",
                str(prefix / "e.txt") + " source2 x ==",
                str(prefix / "f.txt") + " source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                shelephant.dataset.cp(
                    [
                        "source2",
                        "source1",
                        str(prefix / "e.txt"),
                        str(prefix / "f.txt"),
                        "-q",
                        "--force",
                    ]
                )

            with cwd(source1):
                self.assertTrue(os.path.isfile(prefix / "e.txt"))
                self.assertTrue(os.path.isfile(prefix / "f.txt"))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / "a.txt") + " source1 == ==",
                str(prefix / "b.txt") + " source1 == ==",
                str(prefix / "c.txt") + " source1 == ==",
                str(prefix / "d.txt") + " source1 == ==",
                str(prefix / "e.txt") + " source1 == ==",
                str(prefix / "f.txt") + " source1 == ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

    def test_prefix_cp_both(self):
        with tempdir():
            dataset = pathlib.Path("dataset")
            source1 = pathlib.Path("source1")
            source2 = pathlib.Path("source2")
            prefix = pathlib.Path("prefix")
            mydir = pathlib.Path("mydir")

            dataset.mkdir()
            source1.mkdir(parents=True)
            source2.mkdir(parents=True)

            with cwd(source1):
                mydir.mkdir()
                with cwd(mydir):
                    files = ["a.txt", "b.txt", "c.txt", "d.txt"]
                    create_dummy_files(files)

            with cwd(source2):
                create_dummy_files(["a.txt", "b.txt"])
                create_dummy_files(["e.txt", "f.txt"], slice(6, None, None))

            with cwd(dataset):
                shelephant.dataset.init([])
                shelephant.dataset.add(
                    ["source1", "../source1", "--prefix", str(prefix), "--rglob", "*.txt", "-q"]
                )
                shelephant.dataset.add(
                    [
                        "source2",
                        "../source2",
                        "--prefix",
                        str(prefix / mydir),
                        "--rglob",
                        "*.txt",
                        "-q",
                    ]
                )

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / mydir / "a.txt") + " source1 == ==",
                str(prefix / mydir / "b.txt") + " source1 == ==",
                str(prefix / mydir / "c.txt") + " source1 == x",
                str(prefix / mydir / "d.txt") + " source1 == x",
                str(prefix / mydir / "e.txt") + " source2 x ==",
                str(prefix / mydir / "f.txt") + " source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                shelephant.dataset.cp(
                    [
                        "source1",
                        "source2",
                        str(prefix / mydir / "c.txt"),
                        str(prefix / mydir / "d.txt"),
                        "-q",
                        "--force",
                    ]
                )

            with cwd(source2):
                self.assertTrue(os.path.isfile("c.txt"))
                self.assertTrue(os.path.isfile("d.txt"))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / mydir / "a.txt") + " source1 == ==",
                str(prefix / mydir / "b.txt") + " source1 == ==",
                str(prefix / mydir / "c.txt") + " source1 == ==",
                str(prefix / mydir / "d.txt") + " source1 == ==",
                str(prefix / mydir / "e.txt") + " source2 x ==",
                str(prefix / mydir / "f.txt") + " source2 x ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)

            with cwd(dataset):
                shelephant.dataset.cp(
                    [
                        "source2",
                        "source1",
                        str(prefix / mydir / "e.txt"),
                        str(prefix / mydir / "f.txt"),
                        "-q",
                        "--force",
                    ]
                )

            with cwd(source1):
                self.assertTrue(os.path.isfile(mydir / "e.txt"))
                self.assertTrue(os.path.isfile(mydir / "f.txt"))

            with cwd(dataset), contextlib.redirect_stdout(io.StringIO()) as sio:
                shelephant.dataset.status(["--table", "PLAIN_COLUMNS"])

            expect = [
                str(prefix / mydir / "a.txt") + " source1 == ==",
                str(prefix / mydir / "b.txt") + " source1 == ==",
                str(prefix / mydir / "c.txt") + " source1 == ==",
                str(prefix / mydir / "d.txt") + " source1 == ==",
                str(prefix / mydir / "e.txt") + " source1 == ==",
                str(prefix / mydir / "f.txt") + " source1 == ==",
            ]
            ret = _plain(sio.getvalue())[1:]
            self.assertEqual(ret, expect)


if __name__ == "__main__":
    unittest.main()
