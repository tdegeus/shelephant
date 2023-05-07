import os
import pathlib
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

import numpy as np

import shelephant
from shelephant import shelephant_dump


@contextmanager
def tempdir():
    """
    Set the cwd to a temporary directory.
    """

    origin = Path().absolute()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.chdir(tmp)
            yield
        finally:
            os.chdir(origin)


def create_dummy_files(filenames: list[str]) -> dict[str]:
    """
    Create dummy files in the current directory.

    :param list filenames: List of filenames.
    :return: sha256 checksums of the created files.
    """

    content = {
        "foo": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        "bar": "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        "a": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
        "b": "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
        "c": "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6",
        "d": "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",
        "e": "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca046dea",
        "f": "252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111",
        "g": "cd0aa9856147b6c5b4ff2b7dfee5da20aa38253099ef1b4a64aced233c9afe29",
    }

    assert len(filenames) <= len(content)

    ret = {}
    for filename, (content, sha) in zip(filenames, content.items()):
        pathlib.Path(filename).write_text(content)
        ret[filename] = sha

    return ret


def run(cmd, verbose=False):
    return subprocess.check_output(cmd, shell=True).decode("utf-8")


class Test_tools(unittest.TestCase):
    def test_flatten(self):
        arg = [1, [2, 2, 2], 4]
        ret = [1, 2, 2, 2, 4]

        self.assertEqual(ret, shelephant.convert.flatten(arg))

    def test_squash(self):
        arg = {"foo": [1, 2], "bar": {"foo": [3, 4], "bar": 5}}
        ret = [1, 2, 3, 4, 5]

        self.assertEqual(ret, shelephant.convert.squash(arg))

    def test_deepest_dirs(self):
        dirnames = [
            "foo/bar",
            "foo/bar/mydir",
            "bar/mydir",
            "bar",
            "bar/mydir2",
            "foo/bar/mydir/deep",
            "foo/bar/mydir/deep/deeper",
            "foo/bar/mydir/deep/also",
            "foo/shallow",
        ]

        ret = shelephant.path.filter_deepest(dirnames)

        d = [
            "bar/mydir",
            "bar/mydir2",
            "foo/bar/mydir/deep/deeper",
            "foo/bar/mydir/deep/also",
            "foo/shallow",
        ]

        self.assertEqual(sorted(ret), sorted(d))


class Test_shelephant_dump(unittest.TestCase):
    def test_checksum(self):
        with tempdir():
            files = ["foo.txt", "bar.txt"]
            check = create_dummy_files(files)

            shelephant_dump(["-i"] + files)

            data = shelephant.yaml.read("shelephant_dump.yaml")
            data = {item["path"]: item["sha256"] for item in data}

            for filename in files:
                self.assertEqual(check[filename], data[filename])

    def test_find(self):
        with tempdir():
            files = ["foo.txt", "bar.txt", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)

            shelephant_dump(["-i", "-c", "find . -name '*.txt'"])
            data = shelephant.yaml.read("shelephant_dump.yaml")
            data = {item["path"]: item["sha256"] for item in data}

            for filename in files:
                self.assertEqual(check[filename], data[filename])

    def test_append(self):
        with tempdir():
            files = ["foo.pdf", "bar.pdf", "a.txt", "b.txt", "c.txt", "d.txt"]
            check = create_dummy_files(files)
            pdf = [i for i in files if i.endswith(".pdf")]
            [i for i in files if i.endswith(".txt")]

            # plain

            shelephant_dump(pdf)
            data = shelephant.yaml.read("shelephant_dump.yaml")
            self.assertEqual(data, pdf)

            shelephant_dump(["-a", "-c", "find . -name '*.txt'"])
            data = shelephant.yaml.read("shelephant_dump.yaml")
            self.assertEqual(sorted(data), sorted(files))

            # with details

            shelephant_dump(["-f", "-i"] + pdf)
            data = shelephant.yaml.read("shelephant_dump.yaml")
            data = {item["path"]: item["sha256"] for item in data}

            for filename in pdf:
                self.assertEqual(check[filename], data[filename])

            shelephant_dump(["-a", "-i", "-c", "find . -name '*.txt'"])
            data = shelephant.yaml.read("shelephant_dump.yaml")
            data = {item["path"]: item["sha256"] for item in data}

            for filename in files:
                self.assertEqual(check[filename], data[filename])

    def test_exclude(self):
        with tempdir():
            shelephant_dump(["a.txt", "b.bak", "c.h5", "-E", ".bak"])
            data = shelephant.yaml.read("shelephant_dump.yaml")

        self.assertEqual(data, ["a.txt", "c.h5"])


# class Test_extract(unittest.TestCase):
#     def test_single_path(self):
#         data = {
#             "foo": ["foo.txt", "bar.txt"],
#             "bar": ["foo.pdf", "bar.pdf"],
#             "key": ["foo.key", "bar.key"],
#         }

#         shelephant.yaml.dump("dump.yaml", data, force=True)

#         run('shelephant_extract -f dump.yaml "foo"')

#         self.assertEqual(shelephant.yaml.read("dump.yaml"), ["foo.txt", "bar.txt"])

#         os.remove("dump.yaml")

#     def test_multiple_paths(self):
#         data = {
#             "foo": ["foo.txt", "bar.txt"],
#             "bar": ["foo.pdf", "bar.pdf"],
#             "key": ["foo.key", "bar.key"],
#             "sub": {
#                 "foo": ["foo.txt", "bar.txt"],
#                 "bar": ["foo.pdf", "bar.pdf"],
#                 "key": ["foo.key", "bar.key"],
#             },
#         }

#         shelephant.yaml.dump("dump.yaml", data, force=True)

#         run('shelephant_extract -f dump.yaml "/sub/foo" "foo"')

#         self.assertEqual(
#             shelephant.yaml.read("dump.yaml"),
#             {"foo": ["foo.txt", "bar.txt"], "sub": {"foo": ["foo.txt", "bar.txt"]}},
#         )

#         os.remove("dump.yaml")

#     def test_multiple_paths_squash(self):
#         data = {
#             "foo": ["foo.txt", "bar.txt"],
#             "bar": ["foo.pdf", "bar.pdf"],
#             "key": ["foo.key", "bar.key"],
#             "sub": {
#                 "foo": ["foo2.txt", "bar2.txt"],
#                 "bar": ["foo2.pdf", "bar2.pdf"],
#                 "key": ["foo2.key", "bar2.key"],
#             },
#         }

#         shelephant.yaml.dump("dump.yaml", data, force=True)

#         run('shelephant_extract -f --squash dump.yaml "/sub/foo" "foo"')

#         self.assertEqual(
#             shelephant.yaml.read("dump.yaml"),
#             ["foo2.txt", "bar2.txt", "foo.txt", "bar.txt"],
#         )

#         os.remove("dump.yaml")


# class Test_merge(unittest.TestCase):
#     def test_basic(self):
#         pathlib.Path("foo.txt").write_text("foo")
#         pathlib.Path("bar.txt").write_text("bar")

#         shelephant_dump(["-o", "main.yaml", "foo.txt"])
#         shelephant_dump(["-o", "branch.yaml", "bar.txt"])
#         run("shelephant_merge -f branch.yaml main.yaml")

#         self.assertEqual(shelephant.yaml.read("main.yaml"), ["foo.txt", "bar.txt"])

#         os.remove("foo.txt")
#         os.remove("bar.txt")
#         os.remove("main.yaml")
#         os.remove("branch.yaml")

#         os.mkdir("dira")
#         os.mkdir("dirb")

#         with open("dira/foo.txt", "w") as file:
#             file.write("foo")

#         with open("dira/bar.txt", "w") as file:
#             file.write("bar")

#         with open("dirb/foo.txt", "w") as file:
#             file.write("foo")

#         with open("dirb/bar.txt", "w") as file:
#             file.write("bar")

#         shelephant_dump(["-o", "dira/dump.yaml", "dira/foo.txt", "dira/bar.txt"])
#         shelephant_dump(["-o", "dirb/dump.yaml", "dirb/foo.txt", "dirb/bar.txt"])
#         run("shelephant_merge -f dira/dump.yaml dirb/dump.yaml")

#         self.assertEqual(
#             shelephant.yaml.read("dirb/dump.yaml"),
#             ["foo.txt", "bar.txt", "../dira/foo.txt", "../dira/bar.txt"],
#         )

#         shutil.rmtree("dira")
#         shutil.rmtree("dirb")


# class Test_hostinfo(unittest.TestCase):
#     def test_basic(self):
#         for dirname in ["mysrc", "mydest"]:
#             if os.path.isdir(dirname):
#                 shutil.rmtree(dirname)

#         os.mkdir("mysrc")
#         os.mkdir("mydest")

#         with open("mysrc/foo.txt", "w") as file:
#             file.write("foo")

#         with open("mysrc/bar.txt", "w") as file:
#             file.write("bar")

#         shelephant_dump(["-f", "-s", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt"])
#         run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
#         run(
#             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
#         )
#         run("shelephant_get -f -q mydest/hostinfo.yaml")
#         shelephant_dump(["-f", "-s", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt"])
#         run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

#         self.assertEqual(
#             shelephant.yaml.read("mysrc/files.yaml"),
#             shelephant.yaml.read("mydest/files.yaml"),
#         )
#         self.assertEqual(
#             shelephant.yaml.read("mysrc/checksum.yaml"),
#             shelephant.yaml.read("mydest/checksum.yaml"),
#         )

#         shutil.rmtree("mysrc")
#         shutil.rmtree("mydest")

#     def test_remove(self):
#         pathlib.Path("foo.txt").write_text("foo")
#         pathlib.Path("bar.txt").write_text("bar")

#         keys = [
#             "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
#             "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
#         ]

#         shelephant_dump(["-f", "foo.txt", "bar.txt"])
#         run("shelephant_checksum -f -q")
#         run("shelephant_hostinfo --force -f -c")
#         run("shelephant_hostinfo --force --remove bar.txt")
#         data = shelephant.yaml.read("shelephant_hostinfo.yaml")

#         self.assertEqual(data["files"], ["foo.txt"])
#         self.assertEqual(data["checksum"], [keys[0]])

#         os.remove("foo.txt")
#         os.remove("bar.txt")
#         os.remove("shelephant_dump.yaml")
#         os.remove("shelephant_checksum.yaml")
#         os.remove("shelephant_hostinfo.yaml")


# class Test_get(unittest.TestCase):
#     def test_basic(self):
#         for dirname in ["mysrc", "mydest"]:
#             if os.path.isdir(dirname):
#                 shutil.rmtree(dirname)

#         os.mkdir("mysrc")
#         os.mkdir("mydest")

#         with open("mysrc/foo.txt", "w") as file:
#             file.write("foo")

#         with open("mysrc/bar 1.txt", "w") as file:
#             file.write("bar")

#         operations = [
#             "bar 1.txt -> bar 1.txt",
#             "foo.txt   -> foo.txt",
#         ]

#         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar 1.txt"])
#         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
#         output = run(
#             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
#         )
#         output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

#         self.assertEqual(list(filter(None, output.split("\n"))), operations)

#         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar 1.txt"])
#         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

#         self.assertEqual(
#             shelephant.yaml.read("mysrc/files.yaml"),
#             shelephant.yaml.read("mydest/files.yaml"),
#         )
#         self.assertEqual(
#             shelephant.yaml.read("mysrc/checksum.yaml"),
#             shelephant.yaml.read("mydest/checksum.yaml"),
#         )

#         shutil.rmtree("mysrc")
#         shutil.rmtree("mydest")

#     def test_partial(self):
#         for dirname in ["mysrc", "mydest"]:
#             if os.path.isdir(dirname):
#                 shutil.rmtree(dirname)

#         os.mkdir("mysrc")
#         os.mkdir("mydest")

#         with open("mysrc/foo.txt", "w") as file:
#             file.write("foo")

#         with open("mysrc/bar.txt", "w") as file:
#             file.write("bar")

#         shutil.copy("mysrc/foo.txt", "mydest/foo.txt")

#         operations = [
#             "bar.txt -> bar.txt",
#             "foo.txt == foo.txt",
#         ]

#         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt"])
#         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
#         output = run(
#             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
#         )
#         output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

#         self.assertEqual(list(filter(None, output.split("\n"))), operations)

#         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt"])
#         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

#         self.assertEqual(
#             shelephant.yaml.read("mysrc/files.yaml"),
#             shelephant.yaml.read("mydest/files.yaml"),
#         )
#         self.assertEqual(
#             shelephant.yaml.read("mysrc/checksum.yaml"),
#             shelephant.yaml.read("mydest/checksum.yaml"),
#         )

#         shutil.rmtree("mysrc")
#         shutil.rmtree("mydest")

#     def test_partial_localchecksum(self):
#         for dirname in ["mysrc", "mydest"]:
#             if os.path.isdir(dirname):
#                 shutil.rmtree(dirname)

#         os.mkdir("mysrc")
#         os.mkdir("mydest")

#         with open("mysrc/foo.txt", "w") as file:
#             file.write("foo")

#         with open("mysrc/bar.txt", "w") as file:
#             file.write("bar")

#         with open("mysrc/car.txt", "w") as file:
#             file.write("car")

#         with open("mysrc/dog.txt", "w") as file:
#             file.write("dog")

#         shutil.copy("mysrc/foo.txt", "mydest/foo.txt")
#         shutil.copy("mysrc/dog.txt", "mydest/dog.txt")

#         operations = [
#             "bar.txt -> bar.txt",
#             "car.txt -> car.txt",
#             "dog.txt == dog.txt",
#             "foo.txt == foo.txt",
#         ]

#         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt", "mysrc/car.txt", "mysrc/dog.txt"])
#         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
#         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt", "mydest/car.txt", "mydest/dog.txt"])
#         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
#         output = run(
#             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
#         )
#         output = run(
#             "shelephant_hostinfo -o mydest/local.yaml -f mydest/files.yaml -c mydest/checksum.yaml"
#         )
#         output = run(
#             "shelephant_get -f -d -q --colors none -l mydest/local.yaml mydest/hostinfo.yaml"
#         )

#         self.assertEqual(list(filter(None, output.split("\n"))), operations)

#         output = shelephant_dump(["-f", "-s", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt", "mydest/car.txt", "mydest/dog.txt"])
#         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

#         self.assertEqual(
#             shelephant.yaml.read("mysrc/files.yaml"),
#             shelephant.yaml.read("mydest/files.yaml"),
#         )
#         self.assertEqual(
#             shelephant.yaml.read("mysrc/checksum.yaml"),
#             shelephant.yaml.read("mydest/checksum.yaml"),
#         )

#         shutil.rmtree("mysrc")
#         shutil.rmtree("mydest")

#     def test_partial_rsync(self):
#         for dirname in ["mysrc", "mydest"]:
#             if os.path.isdir(dirname):
#                 shutil.rmtree(dirname)

#         os.mkdir("mysrc")
#         os.mkdir("mydest")

#         with open("mysrc/foo.txt", "w") as file:
#             file.write("foo")

#         with open("mysrc/bar.txt", "w") as file:
#             file.write("bar")

#         shutil.copy2("mysrc/foo.txt", "mydest/foo.txt")

#         operations = [
#             "bar.txt -> bar.txt",
#             "foo.txt == foo.txt",
#         ]

#         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt"])
#         output = run("shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml")
#         output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

#         self.assertEqual(list(filter(None, output.split("\n"))), operations)

#         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt"])
#         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
#         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

#         self.assertEqual(
#             shelephant.yaml.read("mysrc/files.yaml"),
#             shelephant.yaml.read("mydest/files.yaml"),
#         )
#         self.assertEqual(
#             shelephant.yaml.read("mysrc/checksum.yaml"),
#             shelephant.yaml.read("mydest/checksum.yaml"),
#         )

#         shutil.rmtree("mysrc")
#         shutil.rmtree("mydest")


# # class Test_send(unittest.TestCase):
# #     def test_basic(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         with open("mydest/foobar.txt", "w") as file:
# #             file.write("foobar")

# #         operations = [
# #             "bar.txt -> bar.txt",
# #             "foo.txt -> foo.txt",
# #         ]

# #         shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# #         run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
# #         output = run(
# #             "shelephant_send -f -d -q --colors none mysrc/files.yaml shelephant_hostinfo.yaml"
# #         )

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         os.remove("mydest/foobar.txt")

# #         shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")
# #         os.remove("shelephant_hostinfo.yaml")

# #     def test_empty_remote(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         operations = [
# #             "bar.txt -> bar.txt",
# #             "foo.txt -> foo.txt",
# #         ]

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         output = run("shelephant_hostinfo --force -o hostinfo.yaml -p mydest")
# #         output = run("shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")
# #         output = run("shelephant_checksum -f -q -o mysrc/checksum.yaml mysrc/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")
# #         os.remove("hostinfo.yaml")

# #     def test_partial(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         shutil.copy("mysrc/foo.txt", "mydest/foo.txt")

# #         operations = [
# #             "bar.txt -> bar.txt",
# #             "foo.txt == foo.txt",
# #         ]

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         output = shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# #         output = run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
# #         output = run(
# #             "shelephant_send -f -d -q --colors none mysrc/files.yaml shelephant_hostinfo.yaml"
# #         )

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")
# #         os.remove("shelephant_hostinfo.yaml")

# #     def test_partial_localchecksum(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         with open("mysrc/car.txt", "w") as file:
# #             file.write("car")

# #         with open("mysrc/dog.txt", "w") as file:
# #             file.write("dog")

# #         shutil.copy("mysrc/foo.txt", "mydest/foo.txt")
# #         shutil.copy("mysrc/dog.txt", "mydest/dog.txt")

# #         operations = [
# #             "bar.txt -> bar.txt",
# #             "car.txt -> car.txt",
# #             "dog.txt == dog.txt",
# #             "foo.txt == foo.txt",
# #         ]

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         output = shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# #         output = run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
# #         output = run(
# #             "shelephant_hostinfo --force -o local.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
# #         )
# #         output = run(
# #             " ".join(
# #                 [
# #                     "shelephant_send",
# #                     "-f",
# #                     "-d",
# #                     "-q",
# #                     "--colors none",
# #                     "-l local.yaml",
# #                     "mysrc/files.yaml",
# #                     "shelephant_hostinfo.yaml",
# #                 ]
# #             )
# #         )

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")
# #         os.remove("shelephant_hostinfo.yaml")
# #         os.remove("local.yaml")

# #     def test_partial_rsync(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         shutil.copy2("mysrc/foo.txt", "mydest/foo.txt")

# #         operations = [
# #             "bar.txt -> bar.txt",
# #             "foo.txt == foo.txt",
# #         ]

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         output = run("shelephant_hostinfo --force -o hostinfo.yaml -p mydest")
# #         output = run("shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")
# #         os.remove("hostinfo.yaml")


# # class Test_mv(unittest.TestCase):
# #     def test_basic(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         shelephant_dump(["-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         run("shelephant_mv -f -q mysrc/files.yaml mydest")
# #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")


# # class Test_cp(unittest.TestCase):
# #     def test_basic(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         shelephant_dump(["-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         run("shelephant_cp -f -q mysrc/files.yaml mydest")
# #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )
# #         self.assertTrue(os.path.isfile("mysrc/foo.txt"))
# #         self.assertTrue(os.path.isfile("mysrc/bar.txt"))

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")

# #     def test_rsync(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.log", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.log", "w") as file:
# #             file.write("bar")

# #         shutil.copy2("mysrc/foo.log", "mydest/foo.log")

# #         operations = [
# #             "bar.log -> bar.log",
# #             "foo.log == foo.log",
# #         ]

# #         output = shelephant_dump(["shelephant_dump", "-o", "mysrc/files.yaml", "mysrc/*.log"])
# #         output = run("shelephant_cp -f -d -q --colors none mysrc/files.yaml mydest")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["shelephant_dump", "--sort", "-o", "mydest/files.yaml", "mydest/*.log"])
# #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/files.yaml"),
# #             shelephant.yaml.read("mydest/files.yaml"),
# #         )
# #         self.assertEqual(
# #             shelephant.yaml.read("mysrc/checksum.yaml"),
# #             shelephant.yaml.read("mydest/checksum.yaml"),
# #         )
# #         self.assertTrue(os.path.isfile("mysrc/foo.log"))
# #         self.assertTrue(os.path.isfile("mysrc/bar.log"))

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")

# #     def test_nested(self):
# #         for dirname in ["mysrc", "mybak"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.makedirs("mysrc/foo/foo/foo")

# #         with open("mysrc/foo.log", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/foo/foo.log", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/foo/foo/foo.log", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/foo/foo/foo/foo.log", "w") as file:
# #             file.write("foo")

# #         operations = [
# #             "mysrc/foo.log             -> mysrc/foo.log",
# #             "mysrc/foo/foo.log         -> mysrc/foo/foo.log",
# #             "mysrc/foo/foo/foo.log     -> mysrc/foo/foo/foo.log",
# #             "mysrc/foo/foo/foo/foo.log -> mysrc/foo/foo/foo/foo.log",
# #         ]

# #         output = shelephant_dump(["-f", "-s `find . -iname '*.log'`"])
# #         output = run("shelephant_cp -f -d -q --colors none mybak")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         self.assertTrue(os.path.isfile("mybak/mysrc/foo.log"))
# #         self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo.log"))
# #         self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo/foo.log"))
# #         self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo/foo/foo.log"))

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mybak")


# # class Test_rm(unittest.TestCase):
# #     def test_basic(self):
# #         with open("foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("bar.txt", "w") as file:
# #             file.write("bar")

# #         shelephant_dump(["-f", "foo.txt", "bar.txt"])
# #         run("shelephant_rm -f shelephant_dump.yaml")

# #         self.assertFalse(os.path.isfile("foo.txt"))
# #         self.assertFalse(os.path.isfile("bar.txt"))

# #         os.remove("shelephant_dump.yaml")


# # class Test_diff(unittest.TestCase):
# #     def test_basic(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar.txt", "w") as file:
# #             file.write("bar")

# #         with open("mydest/bar.txt", "w") as file:
# #             file.write("foobar")

# #         with open("mydest/foobar.txt", "w") as file:
# #             file.write("foobar")

# #         shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# #         run("shelephant_diff mysrc/files.yaml mydest/files.yaml --yaml mysrc/diff.yaml")

# #         data = shelephant.yaml.read("mysrc/diff.yaml")
# #         expect = {
# #             "==": [],
# #             "!=": ["bar.txt"],
# #             "->": ["foo.txt"],
# #             "<-": ["foobar.txt"],
# #         }

# #         self.assertDictEqual(data, expect)

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")


# # class Test_parse(unittest.TestCase):
# #     def test_basic(self):
# #         with open("foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("bar.txt", "w") as file:
# #             file.write("bar")

# #         shelephant_dump(["-f", "foo.txt", "bar.txt"])
# #         output = run("shelephant_parse shelephant_dump.yaml")

# #         self.assertEqual(list(filter(None, output.split("\n"))), ["- foo.txt", "- bar.txt"])

# #         os.remove("shelephant_dump.yaml")
# #         os.remove("foo.txt")
# #         os.remove("bar.txt")


if __name__ == "__main__":
    unittest.main()
