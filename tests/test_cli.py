import contextlib
import io
import os
import pathlib
import re
import unittest

import shelephant
from shelephant import shelephant_cp
from shelephant import shelephant_dump
from shelephant import shelephant_hostinfo
from shelephant import shelephant_mv
from shelephant import shelephant_parse
from shelephant._tests import create_dummy_files
from shelephant.search import cwd
from shelephant.search import tempdir

has_ssh = shelephant.ssh.has_keys_set("localhost")


class Test_shelephant_parse(unittest.TestCase):
    def test_basic(self):
        """
        shelephant_parse <file.yaml>
        """
        with tempdir(), contextlib.redirect_stdout(io.StringIO()) as sio:
            files = ["foo.txt", "bar.txt"]
            create_dummy_files(files)
            shelephant_dump(["-i"] + files)
            check = pathlib.Path(shelephant.f_dump).read_text()
            shelephant_parse([shelephant.f_dump])

        self.assertEqual(sio.getvalue().strip(), check.strip())


class Test_shelephant_dump(unittest.TestCase):
    def test_checksum(self):
        with tempdir():
            files = ["foo.txt", "bar.txt"]
            check = create_dummy_files(files)
            shelephant_dump(["-i"] + files)
            data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)
            self.assertTrue(check == data)

    def test_find(self):
        with tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            shelephant_dump(["-i", "-c", "find . -name '*.txt'"])
            data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)
            self.assertTrue(check == data)

    def test_append(self):
        with tempdir():
            files = ["foo.pdf", "bar.pdf", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            pdf = [i for i in files if i.endswith(".pdf")]

            # plain

            shelephant_dump(pdf)
            data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)
            self.assertEqual(data.files(info=False), pdf)

            shelephant_dump(["-a", "-c", "find . -name '*.txt'"])
            data = shelephant.dataset.Location.from_yaml(shelephant.f_dump).sort()
            self.assertEqual(data.files(info=False), sorted(files))

            # with details

            shelephant_dump(["-f", "-i"] + pdf)
            data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)
            self.assertEqual(data.files(info=False), pdf)

            shelephant_dump(["-a", "-i", "-c", "find . -name '*.txt'"])
            data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)
            self.assertTrue(check == data)


class Test_shelephant_cp(unittest.TestCase):
    def test_basic(self):
        """
        shelephant_cp <sourceinfo.yaml> <dest_dirname>
        """
        with tempdir(), contextlib.redirect_stdout(io.StringIO()) as sio:
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)
                args = [shelephant.f_dump, "../dest"]
                shelephant_cp(["-n", "--colors", "none"] + args)
                shelephant_cp(["-f", "--quiet"] + args)

            data = shelephant.dataset.Location(root="dest", files=files).getinfo()
            self.assertTrue(check == data)

        expect = [
            "bar.txt => bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
            "foo.txt == foo.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)

    def test_destinfo(self):
        """
        shelephant_cp <sourceinfo.yaml> <destinfo.yaml>
        """
        with tempdir(), contextlib.redirect_stdout(io.StringIO()) as sio:
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)
                shelephant_hostinfo(["../dest"])
                args = [shelephant.f_dump, shelephant.f_hostinfo]
                shelephant_cp(["-n", "--colors", "none"] + args)
                shelephant_cp(["-f", "--quiet"] + args)

            data = shelephant.dataset.Location(root="dest", files=files).getinfo()
            self.assertTrue(check == data)

        expect = [
            "bar.txt => bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
            "foo.txt == foo.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)

    def test_destinfo_sha256(self):
        """
        shelephant_cp <sourceinfo.yaml> <destinfo.yaml>
        """
        with tempdir(), contextlib.redirect_stdout(io.StringIO()) as sio:
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))
                shelephant_dump(["-i", "foo.txt", "bar.txt"])

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(["-i"] + files)
                shelephant_hostinfo(["../dest", "-d"])
                args = [shelephant.f_dump, shelephant.f_hostinfo]
                shelephant_cp(["-n", "--colors", "none"] + args)
                shelephant_cp(["-f", "--quiet"] + args)

            data = shelephant.dataset.Location(root="dest", files=files).getinfo()
            self.assertTrue(check == data)

        expect = [
            "bar.txt => bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
            "foo.txt == foo.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)

    def test_sourceinfo(self):
        """
        shelephant_cp <sourceinfo.yaml> <dest_dirname>
        """
        with tempdir(), contextlib.redirect_stdout(io.StringIO()) as sio:
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)

            with cwd("dest"):
                shelephant_hostinfo(["../src", "-d"])
                args = [shelephant.f_hostinfo, "."]
                shelephant_cp(["-n", "--colors", "none"] + args)
                shelephant_cp(["-f", "--quiet"] + args)
                shelephant_dump(["-i", "-c", "find . -name '*.txt'"])
                data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)

            self.assertTrue(check == data)

        expect = [
            "bar.txt => bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
            "foo.txt == foo.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)

    def test_ssh_send(self):
        """
        shelephant_cp <sourceinfo.yaml> <dest_dirname_on_host> --ssh <user@host>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as remote, contextlib.redirect_stdout(
            io.StringIO()
        ) as sio:
            files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
            check = create_dummy_files(files)
            shelephant_dump(files)

            args = [shelephant.f_dump, str(remote), "--ssh", "localhost"]
            shelephant_cp(["-n", "--colors", "none"] + args)
            shelephant_cp(["-f", "--quiet"] + args)
            data = shelephant.dataset.Location(root=remote, files=files).getinfo()

        self.assertTrue(check == data)

        expect = [
            "foo.txt -> foo.txt",
            "bar.txt -> bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)

    def test_ssh_send2(self):
        """
        shelephant_cp <sourceinfo.yaml> <remote_destinfo.yaml>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as remote, contextlib.redirect_stdout(
            io.StringIO()
        ) as sio:
            files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
            check = create_dummy_files(files)
            shelephant_dump(files)
            shelephant_hostinfo([str(remote), "--ssh", "localhost"])

            args = [shelephant.f_dump, shelephant.f_hostinfo]
            shelephant_cp(["-n", "--colors", "none"] + args)
            shelephant_cp(["-f", "--quiet"] + args)
            data = shelephant.dataset.Location(root=remote, files=files).getinfo()

        self.assertTrue(check == data)

        expect = [
            "foo.txt -> foo.txt",
            "bar.txt -> bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)

    def test_ssh_get(self):
        """
        shelephant_cp <remote_sourceinfo.yaml> <dest_dirname>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as remote, contextlib.redirect_stdout(
            io.StringIO()
        ) as sio:
            with cwd(remote):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)

            shelephant_hostinfo([str(remote), "--ssh", "localhost", "-d"])
            args = [shelephant.f_hostinfo, "."]
            shelephant_cp(["-n", "--colors", "none"] + args)
            shelephant_cp(["-f", "--quiet"] + args)
            data = shelephant.dataset.Location(root=".", files=files).getinfo()

        self.assertTrue(check == data)

        expect = [
            "foo.txt -> foo.txt",
            "bar.txt -> bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)


class Test_shelephant_mv(unittest.TestCase):
    def test_basic(self):
        """
        shelephant_mv <sourceinfo.yaml> <dest_dirname>
        """
        with tempdir(), contextlib.redirect_stdout(io.StringIO()) as sio:
            pathlib.Path("src").mkdir()
            pathlib.Path("dest").mkdir()

            with cwd("dest"):
                create_dummy_files(["foo.txt"])
                create_dummy_files(["bar.txt"], keep=slice(2, None, None))

            with cwd("src"):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)
                shelephant_mv(["-n", "--colors", "none", shelephant.f_dump, "../dest"])
                shelephant_mv(["-f", "--quiet", shelephant.f_dump, "../dest"])
                self.assertFalse(any([os.path.exists(f) for f in files]))

            data = shelephant.dataset.Location(root="dest", files=files).getinfo()
            self.assertTrue(check == data)

        expect = [
            "foo.txt => foo.txt",
            "bar.txt => bar.txt",
            "more.txt -> more.txt",
            "even_more.txt -> even_more.txt",
        ]
        ret = sio.getvalue()
        ret = list(filter(None, [re.sub(r"\s+", " ", line) for line in ret.splitlines()]))
        self.assertEqual(ret, expect)


if __name__ == "__main__":
    unittest.main()
