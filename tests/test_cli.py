import pathlib
import unittest

import shelephant
from shelephant import shelephant_cp
from shelephant import shelephant_dump
from shelephant import shelephant_hostinfo
from shelephant._tests import create_dummy_files
from shelephant.search import cwd
from shelephant.search import tempdir

has_ssh = shelephant.ssh.has_keys_set("localhost")


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
                shelephant_cp(["-f", "--quiet", shelephant.f_dump, "../dest"])

            data = shelephant.dataset.Location(root="dest", files=files).getinfo()
            self.assertTrue(check == data)

    def test_destinfo(self):
        """
        shelephant_cp <sourceinfo.yaml> <destinfo.yaml>
        """
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
                shelephant_hostinfo(["../dest"])
                shelephant_cp(["-f", "--quiet", shelephant.f_dump, shelephant.f_hostinfo])

            data = shelephant.dataset.Location(root="dest", files=files).getinfo()
            self.assertTrue(check == data)

    def test_sourceinfo(self):
        """
        shelephant_cp <sourceinfo.yaml> <dest_dirname>
        """
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

            with cwd("dest"):
                shelephant_hostinfo(["../src", "-d"])
                shelephant_cp(["-f", "--quiet", shelephant.f_hostinfo, "."])
                shelephant_dump(["-i", "-c", "find . -name '*.txt'"])
                data = shelephant.dataset.Location.from_yaml(shelephant.f_dump)

            self.assertTrue(check == data)

    def test_ssh_send(self):
        """
        shelephant_cp <sourceinfo.yaml> <dest_dirname_on_host> --ssh <user@host>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as remote:
            files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
            check = create_dummy_files(files)
            shelephant_dump(files)

            shelephant_cp(["-f", "--quiet", shelephant.f_dump, str(remote), "--ssh", "localhost"])
            data = shelephant.dataset.Location(root=remote, files=files).getinfo()

        self.assertTrue(check == data)

    def test_ssh_send2(self):
        """
        shelephant_cp <sourceinfo.yaml> <remote_destinfo.yaml>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as remote:
            files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
            check = create_dummy_files(files)
            shelephant_dump(files)
            shelephant_hostinfo([str(remote), "--ssh", "localhost"])

            shelephant_cp(["-f", "--quiet", shelephant.f_dump, shelephant.f_hostinfo])
            data = shelephant.dataset.Location(root=remote, files=files).getinfo()

        self.assertTrue(check == data)

    def test_ssh_get(self):
        """
        shelephant_cp <remote_sourceinfo.yaml> <dest_dirname>
        """
        if not has_ssh:
            raise unittest.SkipTest("'ssh localhost' does not work")

        with tempdir(), shelephant.ssh.tempdir("localhost") as remote:
            with cwd(remote):
                files = ["foo.txt", "bar.txt", "more.txt", "even_more.txt"]
                check = create_dummy_files(files)
                shelephant_dump(files)

            shelephant_hostinfo([str(remote), "--ssh", "localhost", "-d"])
            shelephant_cp(["-f", "--quiet", shelephant.f_hostinfo, "."])
            data = shelephant.dataset.Location(root=".", files=files).getinfo()

        self.assertTrue(check == data)


if __name__ == "__main__":
    unittest.main()
