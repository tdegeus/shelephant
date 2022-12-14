"""
Run as::

    python ssh_test.py HOST PREFIX
"""
import os
import subprocess
import sys
import unittest
from functools import partialmethod

from tqdm import tqdm

import shelephant

tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)


def run(cmd):
    print(cmd)
    return subprocess.check_output(cmd, shell=True).decode("utf-8")


class Test_ssh(unittest.TestCase):
    def test_all(self):

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt == foo.txt",
        ]

        output = run(
            (
                "shelephant_hostinfo -o myssh_send/shelephant_hostinfo.yaml --force "
                '--host "{:s}" --prefix "{:s}" -f -c'
            ).format(self.HOST, os.path.join(self.PREFIX, "myssh_get"))
        )

        output = run(
            "shelephant_send --detail --colors none --force "
            "myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml"
        )

        output = list(filter(None, output.split("\n")))

        self.assertEqual(output, operations)

        operations = [
            "bar.txt == bar.txt",
            "foo.txt -> foo.txt",
        ]

        output = run(
            (
                "shelephant_hostinfo -o myssh_send/shelephant_hostinfo.yaml --force "
                '--host "{:s}" --prefix "{:s}" -f'
            ).format(self.HOST, os.path.join(self.PREFIX, "myssh_get"))
        )

        output = run(
            "shelephant_send --detail --colors none --force "
            "myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml"
        )

        output = list(filter(None, output.split("\n")))
        self.assertEqual(output, operations)

        operations = {
            "<-": [],
            "->": [],
            "!=": [],
            "==": ["bar.txt", "foo.txt"],
        }

        output = run(
            "shelephant_diff -f --yaml shelephant_diff.yaml "
            "myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml"
        )

        output = shelephant.yaml.read("shelephant_diff.yaml")

        for key in operations:
            self.assertListEqual(output[key], operations[key])

        operations = [
            "bar.txt -> bar.txt",
            "foo.txt == foo.txt",
        ]

        output = run(
            (
                "shelephant_hostinfo -o myssh_get/shelephant_hostinfo.yaml --force "
                '--host "{:s}" --prefix "{:s}" -f -c'
            ).format(self.HOST, os.path.join(self.PREFIX, "myssh_send"))
        )

        output = run(
            "shelephant_get --detail --colors none --force myssh_get/shelephant_hostinfo.yaml"
        )

        output = list(filter(None, output.split("\n")))
        self.assertEqual(output, operations)

        os.remove("myssh_get/bar.txt")


if __name__ == "__main__":

    Test_ssh.PREFIX = sys.argv.pop()
    Test_ssh.HOST = sys.argv.pop()

    unittest.main()
