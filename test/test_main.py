import os
import shutil
import subprocess
import unittest

import numpy as np

import shelephant


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


class Test_checksum(unittest.TestCase):
    def test_basic(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -f foo.txt bar.txt")
        run("shelephant_checksum -f -q shelephant_dump.yaml")
        data = shelephant.yaml.read_item("shelephant_checksum.yaml")

        keys = [
            "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ]

        self.assertEqual(data, keys)

        os.remove("foo.txt")
        os.remove("bar.txt")
        os.remove("shelephant_dump.yaml")
        os.remove("shelephant_checksum.yaml")

    def test_hybrid(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -f foo.txt")
        run("shelephant_checksum -f -q")
        run("shelephant_hostinfo --force -f -c")

        run("shelephant_dump -f foo.txt bar.txt")
        run("shelephant_checksum -f -q -l shelephant_hostinfo.yaml")
        data = shelephant.yaml.read_item("shelephant_checksum.yaml")

        keys = [
            "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ]

        self.assertEqual(data, keys)

        os.remove("foo.txt")
        os.remove("bar.txt")
        os.remove("shelephant_dump.yaml")
        os.remove("shelephant_checksum.yaml")
        os.remove("shelephant_hostinfo.yaml")

    def test_recursive(self):

        letters = ["a", "b", "c", "d", "e", "f", "g"]

        for letter in letters:
            with open(f"{letter:s}.txt", "w") as file:
                file.write(letter)

        files = [f"{letter:s}.txt" for letter in letters]

        keys = [
            "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",  # a
            "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",  # b
            "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6",  # c
            "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",  # d
            "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca046dea",  # e
            "252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111",  # f
            "cd0aa9856147b6c5b4ff2b7dfee5da20aa38253099ef1b4a64aced233c9afe29",  # g
        ]

        run("shelephant_dump -f -s {:s}".format(" ".join(files)))
        run("shelephant_checksum -f -q")

        data = shelephant.yaml.read_item("shelephant_checksum.yaml")

        self.assertEqual(data, keys)

        ifiles = np.arange(len(files))
        np.random.shuffle(ifiles)

        run("shelephant_dump -f {:s}".format(" ".join([files[i] for i in ifiles[:3]])))
        run("shelephant_checksum -f -q")
        run("shelephant_hostinfo --force -f -c")

        np.random.shuffle(ifiles)

        run("shelephant_dump -f {:s}".format(" ".join([files[i] for i in ifiles])))
        run("shelephant_checksum -f -q -l shelephant_hostinfo.yaml")
        run("shelephant_hostinfo --force -f -c")

        run("shelephant_dump -f -s {:s}".format(" ".join(files)))
        run("shelephant_checksum -f -q -l shelephant_hostinfo.yaml")

        data = shelephant.yaml.read_item("shelephant_checksum.yaml")

        self.assertEqual(data, keys)

        for file in files:
            os.remove(file)

        os.remove("shelephant_dump.yaml")
        os.remove("shelephant_checksum.yaml")
        os.remove("shelephant_hostinfo.yaml")


class Test_dump(unittest.TestCase):
    def test_basic(self):

        with open("myfile_foo.txt", "w") as file:
            file.write("foo")

        with open("myfile_bar.txt", "w") as file:
            file.write("bar")

        for dirname in ["mydir"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mydir")

        with open("mydir/myfile_foo.txt", "w") as file:
            file.write("foo")

        with open("mydir/myfile_bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -f -s -o dump_1.yaml myfile_foo.txt myfile_bar.txt")
        run("shelephant_dump -f -s -o dump_2.yaml *.txt")
        run("shelephant_dump -f -s -o dump_3.yaml -c \"find . -maxdepth 1 -iname 'myfile_*.txt'\"")
        run("shelephant_dump -f -s -o mydir/dump_4.yaml mydir/*.txt")

        with open("dump_1.yaml") as file:
            dump_1 = file.read()

        with open("dump_2.yaml") as file:
            dump_2 = file.read()

        with open("dump_3.yaml") as file:
            dump_3 = file.read()

        with open("mydir/dump_4.yaml") as file:
            dump_4 = file.read()

        self.assertEqual(dump_1, dump_2)
        self.assertEqual(dump_1, dump_3)
        self.assertEqual(dump_1, dump_4)

        os.remove("myfile_foo.txt")
        os.remove("myfile_bar.txt")
        os.remove("dump_1.yaml")
        os.remove("dump_2.yaml")
        os.remove("dump_3.yaml")
        shutil.rmtree("mydir")

    def test_append(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        with open("foo.pdf", "w") as file:
            file.write("foo")

        with open("bar.pdf", "w") as file:
            file.write("bar")

        run("shelephant_dump -f foo.txt bar.txt")
        run("shelephant_dump -a foo.pdf bar.pdf")

        self.assertEqual(
            shelephant.yaml.read("shelephant_dump.yaml"),
            ["foo.txt", "bar.txt", "foo.pdf", "bar.pdf"],
        )

        os.remove("foo.txt")
        os.remove("bar.txt")
        os.remove("foo.pdf")
        os.remove("bar.pdf")
        os.remove("shelephant_dump.yaml")


class Test_extract(unittest.TestCase):
    def test_single_path(self):

        data = {
            "foo": ["foo.txt", "bar.txt"],
            "bar": ["foo.pdf", "bar.pdf"],
            "key": ["foo.key", "bar.key"],
        }

        shelephant.yaml.dump("dump.yaml", data, force=True)

        run('shelephant_extract -f dump.yaml "foo"')

        self.assertEqual(shelephant.yaml.read("dump.yaml"), ["foo.txt", "bar.txt"])

        os.remove("dump.yaml")

    def test_multiple_paths(self):

        data = {
            "foo": ["foo.txt", "bar.txt"],
            "bar": ["foo.pdf", "bar.pdf"],
            "key": ["foo.key", "bar.key"],
            "sub": {
                "foo": ["foo.txt", "bar.txt"],
                "bar": ["foo.pdf", "bar.pdf"],
                "key": ["foo.key", "bar.key"],
            },
        }

        shelephant.yaml.dump("dump.yaml", data, force=True)

        run('shelephant_extract -f dump.yaml "/sub/foo" "foo"')

        self.assertEqual(
            shelephant.yaml.read("dump.yaml"),
            {"foo": ["foo.txt", "bar.txt"], "sub": {"foo": ["foo.txt", "bar.txt"]}},
        )

        os.remove("dump.yaml")

    def test_multiple_paths_squash(self):

        data = {
            "foo": ["foo.txt", "bar.txt"],
            "bar": ["foo.pdf", "bar.pdf"],
            "key": ["foo.key", "bar.key"],
            "sub": {
                "foo": ["foo2.txt", "bar2.txt"],
                "bar": ["foo2.pdf", "bar2.pdf"],
                "key": ["foo2.key", "bar2.key"],
            },
        }

        shelephant.yaml.dump("dump.yaml", data, force=True)

        run('shelephant_extract -f --squash dump.yaml "/sub/foo" "foo"')

        self.assertEqual(
            shelephant.yaml.read("dump.yaml"),
            ["foo2.txt", "bar2.txt", "foo.txt", "bar.txt"],
        )

        os.remove("dump.yaml")


class Test_merge(unittest.TestCase):
    def test_basic(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -o main.yaml foo.txt")
        run("shelephant_dump -o branch.yaml bar.txt")
        run("shelephant_merge -f branch.yaml main.yaml")

        self.assertEqual(shelephant.yaml.read("main.yaml"), ["foo.txt", "bar.txt"])

        os.remove("foo.txt")
        os.remove("bar.txt")
        os.remove("main.yaml")
        os.remove("branch.yaml")

        os.mkdir("dira")
        os.mkdir("dirb")

        with open("dira/foo.txt", "w") as file:
            file.write("foo")

        with open("dira/bar.txt", "w") as file:
            file.write("bar")

        with open("dirb/foo.txt", "w") as file:
            file.write("foo")

        with open("dirb/bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -o dira/dump.yaml dira/foo.txt dira/bar.txt")
        run("shelephant_dump -o dirb/dump.yaml dirb/foo.txt dirb/bar.txt")
        run("shelephant_merge -f dira/dump.yaml dirb/dump.yaml")

        self.assertEqual(
            shelephant.yaml.read("dirb/dump.yaml"),
            ["foo.txt", "bar.txt", "../dira/foo.txt", "../dira/bar.txt"],
        )

        shutil.rmtree("dira")
        shutil.rmtree("dirb")


class Test_hostinfo(unittest.TestCase):
    def test_basic(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -f -s -o mysrc/files.yaml mysrc/*.txt")
        run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        run(
            "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
        )
        run("shelephant_get -f -q mydest/hostinfo.yaml")
        run("shelephant_dump -f -s -o mydest/files.yaml mydest/*.txt")
        run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")

    def test_remove(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        keys = [
            "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ]

        run("shelephant_dump -f foo.txt bar.txt")
        run("shelephant_checksum -f -q")
        run("shelephant_hostinfo --force -f -c")
        run("shelephant_hostinfo --force --remove bar.txt")
        data = shelephant.yaml.read("shelephant_hostinfo.yaml")

        self.assertEqual(data["files"], ["foo.txt"])
        self.assertEqual(data["checksum"], [keys[0]])

        os.remove("foo.txt")
        os.remove("bar.txt")
        os.remove("shelephant_dump.yaml")
        os.remove("shelephant_checksum.yaml")
        os.remove("shelephant_hostinfo.yaml")


class Test_get(unittest.TestCase):
    def test_basic(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt -> foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        output = run(
            "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
        )
        output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")

    def test_partial(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        shutil.copy("mysrc/foo.txt", "mydest/foo.txt")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt == foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        output = run(
            "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
        )
        output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")

    def test_partial_localchecksum(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        with open("mysrc/car.txt", "w") as file:
            file.write("car")

        with open("mysrc/dog.txt", "w") as file:
            file.write("dog")

        shutil.copy("mysrc/foo.txt", "mydest/foo.txt")
        shutil.copy("mysrc/dog.txt", "mydest/dog.txt")

        operations = [
            "bar.txt -> bar.txt",
            "car.txt -> car.txt",
            "dog.txt == dog.txt",
            "foo.txt == foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run(
            "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
        )
        output = run(
            "shelephant_hostinfo -o mydest/local.yaml -f mydest/files.yaml -c mydest/checksum.yaml"
        )
        output = run(
            "shelephant_get -f -d -q --colors none -l mydest/local.yaml mydest/hostinfo.yaml"
        )

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump -f -s -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")

    def test_partial_rsync(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        shutil.copy2("mysrc/foo.txt", "mydest/foo.txt")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt == foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml")
        output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")


class Test_send(unittest.TestCase):
    def test_basic(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        with open("mydest/foobar.txt", "w") as file:
            file.write("foobar")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt -> foo.txt",
        ]

        run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
        run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
        output = run(
            "shelephant_send -f -d -q --colors none mysrc/files.yaml shelephant_hostinfo.yaml"
        )

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        os.remove("mydest/foobar.txt")

        run("shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt")
        run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")
        os.remove("shelephant_hostinfo.yaml")

    def test_empty_remote(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt -> foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_hostinfo --force -o hostinfo.yaml -p mydest")
        output = run("shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run("shelephant_checksum -f -q -o mysrc/checksum.yaml mysrc/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")
        os.remove("hostinfo.yaml")

    def test_partial(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        shutil.copy("mysrc/foo.txt", "mydest/foo.txt")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt == foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
        output = run(
            "shelephant_send -f -d -q --colors none mysrc/files.yaml shelephant_hostinfo.yaml"
        )

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")
        os.remove("shelephant_hostinfo.yaml")

    def test_partial_localchecksum(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        with open("mysrc/car.txt", "w") as file:
            file.write("car")

        with open("mysrc/dog.txt", "w") as file:
            file.write("dog")

        shutil.copy("mysrc/foo.txt", "mydest/foo.txt")
        shutil.copy("mysrc/dog.txt", "mydest/dog.txt")

        operations = [
            "bar.txt -> bar.txt",
            "car.txt -> car.txt",
            "dog.txt == dog.txt",
            "foo.txt == foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
        output = run(
            "shelephant_hostinfo --force -o local.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
        )
        output = run(
            " ".join(
                [
                    "shelephant_send",
                    "-f",
                    "-d",
                    "-q",
                    "--colors none",
                    "-l local.yaml",
                    "mysrc/files.yaml",
                    "shelephant_hostinfo.yaml",
                ]
            )
        )

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")
        os.remove("shelephant_hostinfo.yaml")
        os.remove("local.yaml")

    def test_partial_rsync(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        shutil.copy2("mysrc/foo.txt", "mydest/foo.txt")

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt == foo.txt",
        ]

        output = run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        output = run("shelephant_hostinfo --force -o hostinfo.yaml -p mydest")
        output = run("shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt")
        output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")
        os.remove("hostinfo.yaml")


class Test_mv(unittest.TestCase):
    def test_basic(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -o mysrc/files.yaml mysrc/*.txt")
        run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        run("shelephant_mv -f -q mysrc/files.yaml mydest")
        run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")


class Test_cp(unittest.TestCase):
    def test_basic(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -o mysrc/files.yaml mysrc/*.txt")
        run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
        run("shelephant_cp -f -q mysrc/files.yaml mydest")
        run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )
        self.assertTrue(os.path.isfile("mysrc/foo.txt"))
        self.assertTrue(os.path.isfile("mysrc/bar.txt"))

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")

    def test_rsync(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.log", "w") as file:
            file.write("foo")

        with open("mysrc/bar.log", "w") as file:
            file.write("bar")

        shutil.copy2("mysrc/foo.log", "mydest/foo.log")

        operations = [
            "bar.log -> bar.log",
            "foo.log == foo.log",
        ]

        output = run("shelephant_dump -o mysrc/files.yaml mysrc/*.log")
        output = run("shelephant_cp -f -d -q --colors none mysrc/files.yaml mydest")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        output = run("shelephant_dump --sort -o mydest/files.yaml mydest/*.log")
        output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
        output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

        self.assertEqual(
            shelephant.yaml.read("mysrc/files.yaml"),
            shelephant.yaml.read("mydest/files.yaml"),
        )
        self.assertEqual(
            shelephant.yaml.read("mysrc/checksum.yaml"),
            shelephant.yaml.read("mydest/checksum.yaml"),
        )
        self.assertTrue(os.path.isfile("mysrc/foo.log"))
        self.assertTrue(os.path.isfile("mysrc/bar.log"))

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")

    def test_nested(self):

        for dirname in ["mysrc", "mybak"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.makedirs("mysrc/foo/foo/foo")

        with open("mysrc/foo.log", "w") as file:
            file.write("foo")

        with open("mysrc/foo/foo.log", "w") as file:
            file.write("foo")

        with open("mysrc/foo/foo/foo.log", "w") as file:
            file.write("foo")

        with open("mysrc/foo/foo/foo/foo.log", "w") as file:
            file.write("foo")

        operations = [
            "mysrc/foo.log             -> mysrc/foo.log",
            "mysrc/foo/foo.log         -> mysrc/foo/foo.log",
            "mysrc/foo/foo/foo.log     -> mysrc/foo/foo/foo.log",
            "mysrc/foo/foo/foo/foo.log -> mysrc/foo/foo/foo/foo.log",
        ]

        output = run("shelephant_dump -f -s `find . -iname '*.log'`")
        output = run("shelephant_cp -f -d -q --colors none mybak")

        self.assertEqual(list(filter(None, output.split("\n"))), operations)

        self.assertTrue(os.path.isfile("mybak/mysrc/foo.log"))
        self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo.log"))
        self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo/foo.log"))
        self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo/foo/foo.log"))

        shutil.rmtree("mysrc")
        shutil.rmtree("mybak")


class Test_rm(unittest.TestCase):
    def test_basic(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -f foo.txt bar.txt")
        run("shelephant_rm -f shelephant_dump.yaml")

        self.assertFalse(os.path.isfile("foo.txt"))
        self.assertFalse(os.path.isfile("bar.txt"))

        os.remove("shelephant_dump.yaml")


class Test_diff(unittest.TestCase):
    def test_basic(self):

        for dirname in ["mysrc", "mydest"]:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir("mysrc")
        os.mkdir("mydest")

        with open("mysrc/foo.txt", "w") as file:
            file.write("foo")

        with open("mysrc/bar.txt", "w") as file:
            file.write("bar")

        with open("mydest/bar.txt", "w") as file:
            file.write("foobar")

        with open("mydest/foobar.txt", "w") as file:
            file.write("foobar")

        run("shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt")
        run("shelephant_dump --sort -o mydest/files.yaml mydest/*.txt")
        run("shelephant_diff mysrc/files.yaml mydest/files.yaml --yaml mysrc/diff.yaml")

        data = shelephant.yaml.read("mysrc/diff.yaml")
        expect = {
            "==": [],
            "!=": ["bar.txt"],
            "->": ["foo.txt"],
            "<-": ["foobar.txt"],
        }

        self.assertDictEqual(data, expect)

        shutil.rmtree("mysrc")
        shutil.rmtree("mydest")


class Test_parse(unittest.TestCase):
    def test_basic(self):

        with open("foo.txt", "w") as file:
            file.write("foo")

        with open("bar.txt", "w") as file:
            file.write("bar")

        run("shelephant_dump -f foo.txt bar.txt")
        output = run("shelephant_parse shelephant_dump.yaml")

        self.assertEqual(list(filter(None, output.split("\n"))), ["- foo.txt", "- bar.txt"])

        os.remove("shelephant_dump.yaml")
        os.remove("foo.txt")
        os.remove("bar.txt")


if __name__ == "__main__":

    unittest.main()
