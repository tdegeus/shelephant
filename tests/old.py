

# # class Test_extract(unittest.TestCase):
# #     def test_single_path(self):
# #         data = {
# #             "foo": ["foo.txt", "bar.txt"],
# #             "bar": ["foo.pdf", "bar.pdf"],
# #             "key": ["foo.key", "bar.key"],
# #         }

# #         shelephant.yaml.dump("dump.yaml", data, force=True)

# #         run('shelephant_extract -f dump.yaml "foo"')

# #         self.assertEqual(shelephant.yaml.read("dump.yaml"), ["foo.txt", "bar.txt"])

# #         os.remove("dump.yaml")

# #     def test_multiple_paths(self):
# #         data = {
# #             "foo": ["foo.txt", "bar.txt"],
# #             "bar": ["foo.pdf", "bar.pdf"],
# #             "key": ["foo.key", "bar.key"],
# #             "sub": {
# #                 "foo": ["foo.txt", "bar.txt"],
# #                 "bar": ["foo.pdf", "bar.pdf"],
# #                 "key": ["foo.key", "bar.key"],
# #             },
# #         }

# #         shelephant.yaml.dump("dump.yaml", data, force=True)

# #         run('shelephant_extract -f dump.yaml "/sub/foo" "foo"')

# #         self.assertEqual(
# #             shelephant.yaml.read("dump.yaml"),
# #             {"foo": ["foo.txt", "bar.txt"], "sub": {"foo": ["foo.txt", "bar.txt"]}},
# #         )

# #         os.remove("dump.yaml")

# #     def test_multiple_paths_squash(self):
# #         data = {
# #             "foo": ["foo.txt", "bar.txt"],
# #             "bar": ["foo.pdf", "bar.pdf"],
# #             "key": ["foo.key", "bar.key"],
# #             "sub": {
# #                 "foo": ["foo2.txt", "bar2.txt"],
# #                 "bar": ["foo2.pdf", "bar2.pdf"],
# #                 "key": ["foo2.key", "bar2.key"],
# #             },
# #         }

# #         shelephant.yaml.dump("dump.yaml", data, force=True)

# #         run('shelephant_extract -f --squash dump.yaml "/sub/foo" "foo"')

# #         self.assertEqual(
# #             shelephant.yaml.read("dump.yaml"),
# #             ["foo2.txt", "bar2.txt", "foo.txt", "bar.txt"],
# #         )

# #         os.remove("dump.yaml")


# # class Test_merge(unittest.TestCase):
# #     def test_basic(self):
# #         pathlib.Path("foo.txt").write_text("foo")
# #         pathlib.Path("bar.txt").write_text("bar")

# #         shelephant_dump(["-o", "main.yaml", "foo.txt"])
# #         shelephant_dump(["-o", "branch.yaml", "bar.txt"])
# #         run("shelephant_merge -f branch.yaml main.yaml")

# #         self.assertEqual(shelephant.yaml.read("main.yaml"), ["foo.txt", "bar.txt"])

# #         os.remove("foo.txt")
# #         os.remove("bar.txt")
# #         os.remove("main.yaml")
# #         os.remove("branch.yaml")

# #         os.mkdir("dira")
# #         os.mkdir("dirb")

# #         with open("dira/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("dira/bar.txt", "w") as file:
# #             file.write("bar")

# #         with open("dirb/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("dirb/bar.txt", "w") as file:
# #             file.write("bar")

# #         shelephant_dump(["-o", "dira/dump.yaml", "dira/foo.txt", "dira/bar.txt"])
# #         shelephant_dump(["-o", "dirb/dump.yaml", "dirb/foo.txt", "dirb/bar.txt"])
# #         run("shelephant_merge -f dira/dump.yaml dirb/dump.yaml")

# #         self.assertEqual(
# #             shelephant.yaml.read("dirb/dump.yaml"),
# #             ["foo.txt", "bar.txt", "../dira/foo.txt", "../dira/bar.txt"],
# #         )

# #         shutil.rmtree("dira")
# #         shutil.rmtree("dirb")


# # class Test_get(unittest.TestCase):
# #     def test_basic(self):
# #         for dirname in ["mysrc", "mydest"]:
# #             if os.path.isdir(dirname):
# #                 shutil.rmtree(dirname)

# #         os.mkdir("mysrc")
# #         os.mkdir("mydest")

# #         with open("mysrc/foo.txt", "w") as file:
# #             file.write("foo")

# #         with open("mysrc/bar 1.txt", "w") as file:
# #             file.write("bar")

# #         operations = [
# #             "bar 1.txt -> bar 1.txt",
# #             "foo.txt   -> foo.txt",
# #         ]

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar 1.txt"])
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         output = run(
# #             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
# #         )
# #         output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar 1.txt"])
# #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

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

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt"])
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         output = run(
# #             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
# #         )
# #         output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt"])
# #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

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

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt", "mysrc/car.txt", "mysrc/dog.txt"])
# #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# #         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt", "mydest/car.txt", "mydest/dog.txt"])
# #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# #         output = run(
# #             "shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
# #         )
# #         output = run(
# #             "shelephant_hostinfo -o mydest/local.yaml -f mydest/files.yaml -c mydest/checksum.yaml"
# #         )
# #         output = run(
# #             "shelephant_get -f -d -q --colors none -l mydest/local.yaml mydest/hostinfo.yaml"
# #         )

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["-f", "-s", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt", "mydest/car.txt", "mydest/dog.txt"])
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

# #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/foo.txt", "mysrc/bar.txt"])
# #         output = run("shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml")
# #         output = run("shelephant_get -f -d -q --colors none mydest/hostinfo.yaml")

# #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# #         output = shelephant_dump(["--sort", "-o", "mydest/files.yaml", "mydest/foo.txt", "mydest/bar.txt"])
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

# #         shutil.rmtree("mysrc")
# #         shutil.rmtree("mydest")


# # # class Test_send(unittest.TestCase):
# # #     def test_basic(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         with open("mydest/foobar.txt", "w") as file:
# # #             file.write("foobar")

# # #         operations = [
# # #             "bar.txt -> bar.txt",
# # #             "foo.txt -> foo.txt",
# # #         ]

# # #         shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# # #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# # #         run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
# # #         output = run(
# # #             "shelephant_send -f -d -q --colors none mysrc/files.yaml shelephant_hostinfo.yaml"
# # #         )

# # #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# # #         os.remove("mydest/foobar.txt")

# # #         shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/files.yaml"),
# # #             shelephant.yaml.read("mydest/files.yaml"),
# # #         )
# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/checksum.yaml"),
# # #             shelephant.yaml.read("mydest/checksum.yaml"),
# # #         )

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")
# # #         os.remove("shelephant_hostinfo.yaml")

# # #     def test_empty_remote(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         operations = [
# # #             "bar.txt -> bar.txt",
# # #             "foo.txt -> foo.txt",
# # #         ]

# # #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         output = run("shelephant_hostinfo --force -o hostinfo.yaml -p mydest")
# # #         output = run("shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml")

# # #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# # #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")
# # #         output = run("shelephant_checksum -f -q -o mysrc/checksum.yaml mysrc/files.yaml")

# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/files.yaml"),
# # #             shelephant.yaml.read("mydest/files.yaml"),
# # #         )
# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/checksum.yaml"),
# # #             shelephant.yaml.read("mydest/checksum.yaml"),
# # #         )

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")
# # #         os.remove("hostinfo.yaml")

# # #     def test_partial(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         shutil.copy("mysrc/foo.txt", "mydest/foo.txt")

# # #         operations = [
# # #             "bar.txt -> bar.txt",
# # #             "foo.txt == foo.txt",
# # #         ]

# # #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# # #         output = shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# # #         output = run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
# # #         output = run(
# # #             "shelephant_send -f -d -q --colors none mysrc/files.yaml shelephant_hostinfo.yaml"
# # #         )

# # #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# # #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/files.yaml"),
# # #             shelephant.yaml.read("mydest/files.yaml"),
# # #         )
# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/checksum.yaml"),
# # #             shelephant.yaml.read("mydest/checksum.yaml"),
# # #         )

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")
# # #         os.remove("shelephant_hostinfo.yaml")

# # #     def test_partial_localchecksum(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         with open("mysrc/car.txt", "w") as file:
# # #             file.write("car")

# # #         with open("mysrc/dog.txt", "w") as file:
# # #             file.write("dog")

# # #         shutil.copy("mysrc/foo.txt", "mydest/foo.txt")
# # #         shutil.copy("mysrc/dog.txt", "mydest/dog.txt")

# # #         operations = [
# # #             "bar.txt -> bar.txt",
# # #             "car.txt -> car.txt",
# # #             "dog.txt == dog.txt",
# # #             "foo.txt == foo.txt",
# # #         ]

# # #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# # #         output = shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         output = run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")
# # #         output = run("shelephant_hostinfo --force -f mydest/files.yaml -c mydest/checksum.yaml")
# # #         output = run(
# # #             "shelephant_hostinfo --force -o local.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml"
# # #         )
# # #         output = run(
# # #             " ".join(
# # #                 [
# # #                     "shelephant_send",
# # #                     "-f",
# # #                     "-d",
# # #                     "-q",
# # #                     "--colors none",
# # #                     "-l local.yaml",
# # #                     "mysrc/files.yaml",
# # #                     "shelephant_hostinfo.yaml",
# # #                 ]
# # #             )
# # #         )

# # #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# # #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")

# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/files.yaml"),
# # #             shelephant.yaml.read("mydest/files.yaml"),
# # #         )
# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/checksum.yaml"),
# # #             shelephant.yaml.read("mydest/checksum.yaml"),
# # #         )

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")
# # #         os.remove("shelephant_hostinfo.yaml")
# # #         os.remove("local.yaml")

# # #     def test_partial_rsync(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         shutil.copy2("mysrc/foo.txt", "mydest/foo.txt")

# # #         operations = [
# # #             "bar.txt -> bar.txt",
# # #             "foo.txt == foo.txt",
# # #         ]

# # #         output = shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         output = run("shelephant_hostinfo --force -o hostinfo.yaml -p mydest")
# # #         output = run("shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml")

# # #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# # #         output = shelephant_dump(["-f", "--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         output = run("shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml")
# # #         output = run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")

# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/files.yaml"),
# # #             shelephant.yaml.read("mydest/files.yaml"),
# # #         )
# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/checksum.yaml"),
# # #             shelephant.yaml.read("mydest/checksum.yaml"),
# # #         )

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")
# # #         os.remove("hostinfo.yaml")


# # # class Test_mv(unittest.TestCase):
# # #     def test_basic(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         shelephant_dump(["-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         run("shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml")
# # #         run("shelephant_mv -f -q mysrc/files.yaml mydest")
# # #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         run("shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml")

# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/files.yaml"),
# # #             shelephant.yaml.read("mydest/files.yaml"),
# # #         )
# # #         self.assertEqual(
# # #             shelephant.yaml.read("mysrc/checksum.yaml"),
# # #             shelephant.yaml.read("mydest/checksum.yaml"),
# # #         )

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")


# # # class Test_cp(unittest.TestCase):
# # #     def test_nested(self):
# # #         for dirname in ["mysrc", "mybak"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.makedirs("mysrc/foo/foo/foo")

# # #         with open("mysrc/foo.log", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/foo/foo.log", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/foo/foo/foo.log", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/foo/foo/foo/foo.log", "w") as file:
# # #             file.write("foo")

# # #         operations = [
# # #             "mysrc/foo.log             -> mysrc/foo.log",
# # #             "mysrc/foo/foo.log         -> mysrc/foo/foo.log",
# # #             "mysrc/foo/foo/foo.log     -> mysrc/foo/foo/foo.log",
# # #             "mysrc/foo/foo/foo/foo.log -> mysrc/foo/foo/foo/foo.log",
# # #         ]

# # #         output = shelephant_dump(["-f", "-s `find . -iname '*.log'`"])
# # #         output = run("shelephant_cp -f -d -q --colors none mybak")

# # #         self.assertEqual(list(filter(None, output.split("\n"))), operations)

# # #         self.assertTrue(os.path.isfile("mybak/mysrc/foo.log"))
# # #         self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo.log"))
# # #         self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo/foo.log"))
# # #         self.assertTrue(os.path.isfile("mybak/mysrc/foo/foo/foo/foo.log"))

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mybak")


# # # class Test_rm(unittest.TestCase):
# # #     def test_basic(self):
# # #         with open("foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("bar.txt", "w") as file:
# # #             file.write("bar")

# # #         shelephant_dump(["-f", "foo.txt", "bar.txt"])
# # #         run("shelephant_rm -f shelephant_dump.yaml")

# # #         self.assertFalse(os.path.isfile("foo.txt"))
# # #         self.assertFalse(os.path.isfile("bar.txt"))

# # #         os.remove("shelephant_dump.yaml")


# # # class Test_diff(unittest.TestCase):
# # #     def test_basic(self):
# # #         for dirname in ["mysrc", "mydest"]:
# # #             if os.path.isdir(dirname):
# # #                 shutil.rmtree(dirname)

# # #         os.mkdir("mysrc")
# # #         os.mkdir("mydest")

# # #         with open("mysrc/foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("mysrc/bar.txt", "w") as file:
# # #             file.write("bar")

# # #         with open("mydest/bar.txt", "w") as file:
# # #             file.write("foobar")

# # #         with open("mydest/foobar.txt", "w") as file:
# # #             file.write("foobar")

# # #         shelephant_dump(["--sort", "-o", "mysrc/files.yaml", "mysrc/*.txt"])
# # #         shelephant_dump(["--sort", "-o" ,"mydest/files.yaml", "mydest/*.txt"])
# # #         run("shelephant_diff mysrc/files.yaml mydest/files.yaml --yaml mysrc/diff.yaml")

# # #         data = shelephant.yaml.read("mysrc/diff.yaml")
# # #         expect = {
# # #             "==": [],
# # #             "!=": ["bar.txt"],
# # #             "->": ["foo.txt"],
# # #             "<-": ["foobar.txt"],
# # #         }

# # #         self.assertDictEqual(data, expect)

# # #         shutil.rmtree("mysrc")
# # #         shutil.rmtree("mydest")


# # # class Test_parse(unittest.TestCase):
# # #     def test_basic(self):
# # #         with open("foo.txt", "w") as file:
# # #             file.write("foo")

# # #         with open("bar.txt", "w") as file:
# # #             file.write("bar")

# # #         shelephant_dump(["-f", "foo.txt", "bar.txt"])
# # #         output = run("shelephant_parse shelephant_dump.yaml")

# # #         self.assertEqual(list(filter(None, output.split("\n"))), ["- foo.txt", "- bar.txt"])

# # #         os.remove("shelephant_dump.yaml")
# # #         os.remove("foo.txt")
# # #         os.remove("bar.txt")
