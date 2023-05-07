import unittest

import shelephant
from shelephant.detail import create_dummy_files
from shelephant.path import cwd
from shelephant.path import info
from shelephant.path import tempdir


class Test_rsync(unittest.TestCase):
    def test_diff(self):
        a = [
            "a.h5",
            {"path": "b.h5", "sha256": "b"},
            {"path": "c.h5", "sha256": "c"},
            "mydir/e.h5",
        ]

        b = [
            {"path": "a.h5", "sha256": "a"},
            {"path": "b.h5", "sha256": "b"},
            {"path": "c.h5", "sha256": "none"},
        ]

        check = {
            "->": ["mydir/e.h5"],
            "<-": [],
            "==": ["b.h5"],
            "?=": ["a.h5"],
            "!=": ["c.h5"],
        }

        ret = shelephant.dataset.diff(a, b)
        self.assertEqual(ret, check)


if __name__ == "__main__":
    unittest.main()
