"""ssh_test
    Run SSH test.

Usage:
    ssh_test [options] --host=N --prefix=N

Options:
    -r, --host=N        Host name.
    -p, --prefix=M      Path on host.
        --version       Print version.
    -g, --help          Print this help.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
"""
import os
import subprocess

import docopt

import shelephant


def run(cmd):
    print(cmd)
    return subprocess.check_output(cmd, shell=True).decode("utf-8")


args = docopt.docopt(__doc__, version=shelephant.version)

# shelephant_send - local checksum

operations = [
    "bar.txt -> bar.txt",
    "foo.txt == foo.txt",
]

output = run(
    (
        "shelephant_hostinfo -o myssh_send/shelephant_hostinfo.yaml --force "
        '--host "{:s}" --prefix "{:s}" -f -c'
    ).format(args["--host"], os.path.join(args["--prefix"], "myssh_get"))
)

output = run(
    "shelephant_send --detail --colors none --force "
    "myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml"
)

output = list(filter(None, output.split("\n")))
assert output == operations


# shelephant_send - basic

operations = [
    "bar.txt == bar.txt",
    "foo.txt -> foo.txt",
]

output = run(
    (
        "shelephant_hostinfo -o myssh_send/shelephant_hostinfo.yaml --force "
        '--host "{:s}" --prefix "{:s}" -f'
    ).format(args["--host"], os.path.join(args["--prefix"], "myssh_get"))
)

output = run(
    "shelephant_send --detail --colors none --force "
    "myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml"
)

output = list(filter(None, output.split("\n")))
assert output == operations

# shelephant_diff

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
    assert output[key] == operations[key]

# shelephant_get - basic

operations = [
    "bar.txt -> bar.txt",
    "foo.txt == foo.txt",
]

output = run(
    (
        "shelephant_hostinfo -o myssh_get/shelephant_hostinfo.yaml --force "
        '--host "{:s}" --prefix "{:s}" -f -c'
    ).format(args["--host"], os.path.join(args["--prefix"], "myssh_send"))
)

output = run("shelephant_get --detail --colors none --force myssh_get/shelephant_hostinfo.yaml")

output = list(filter(None, output.split("\n")))
assert output == operations

os.remove("myssh_get/bar.txt")
