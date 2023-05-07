import re
import unittest

import shelephant


class Test_path(unittest.TestCase):
    def test_filter_deepest(self):
        check = ["/foo/bar/dir/a", "/foo/bar/dir/b"]
        files = check + ["/foo/bar", "/foo/bar/dir"]
        ret = shelephant.path.filter_deepest(files)
        self.assertEqual(ret, check)

    def test_filter_deepest_2(self):
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

    def test_dirname(self):
        files = ["/foo/bar", "/foo/dir/bar"]
        ret = shelephant.path.dirnames(files)
        self.assertEqual(sorted(ret), ["/foo", "/foo/dir"])


class Test_convert(unittest.TestCase):
    def test_flatten(self):
        arg = [1, [2, 2, 2], 4]
        ret = [1, 2, 2, 2, 4]

        self.assertEqual(ret, shelephant.convert.flatten(arg))

    def test_squash(self):
        arg = {"foo": [1, 2], "bar": {"foo": [3, 4], "bar": 5}}
        ret = [1, 2, 3, 4, 5]

        self.assertEqual(ret, shelephant.convert.squash(arg))


class Test_output(unittest.TestCase):
    def test_copyplan(self):
        ret = shelephant.output.copyplan(
            status={"==": ["skip.txt"], "->": ["right.txt"], "!=": ["overwrite.txt"]},
            display=False,
        )
        expect = [
            "overwrite.txt => overwrite.txt",
            "right.txt -> right.txt",
            "skip.txt == skip.txt",
        ]
        ret = [re.sub(r"\s+", " ", line) for line in ret.splitlines()]
        self.assertEqual(ret, expect)


if __name__ == "__main__":
    unittest.main()
