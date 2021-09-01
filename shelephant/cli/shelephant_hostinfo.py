r"""Collect file information from location (on a remote host).

:usage:

    shelephant_hostinfo [options]

:options:

    -o, --output=arg
        Output YAML-file. [default: shelephant_hostinfo.yaml].

    -r, --host=arg
        Host-name.

    -p, --prefix=arg
        Directory (on host) from which to copy.

    -f, --files=[arg]
        YAML-file with list of files (on remote). [default: shelephant_dump.yaml]

    -c, --checksum=[arg]
        YAML-file with checksums (on remote). [default: shelephant_checksum.yaml]

    --files-key=arg
        Path in the YAML-file, separated by "/". [default: /]

    --checksum-key=arg
        Path in the YAML-file, separated by "/". [default: /]

    --ignore
        Skip basic checks.

    -i, --input=[arg]
        Use host and prefix from existing file. [default: shelephant_hostinfo.yaml]

    --remove=arg...
        Remove paths (and checksums) from existing file.

    --force
        Overwrite output file without prompt.

    --verbose
        Verbose all commands.

    -h, --help
        Show help.

    --version
        Show version.


(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
"""
import argparse
import os
import shutil
import tempfile

import numpy as np

from .. import scp
from .. import version
from .. import yaml
from .defaults import f_checksum
from .defaults import f_dump
from .defaults import f_hostinfo


def remove(data, rm):

    files = np.array(data["files"])
    sorter = np.argsort(files)
    files = files[sorter]
    rm = np.sort(rm)

    if not np.all(np.in1d(rm, files)):
        raise OSError("One or more remove paths not found")

    idx = np.searchsorted(files, rm)
    keep = np.setdiff1d(np.arange(len(files)), sorter[idx])

    files = data["files"]
    checksum = data["checksum"]
    data["files"] = [files[i] for i in keep]
    data["checksum"] = [checksum[i] for i in keep]

    return data


def main_impl():

    # Parse command-line arguments

    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-o", "--output", default=f_hostinfo)
    parser.add_argument("-r", "--host", default=None)
    parser.add_argument("-p", "--prefix", default=None)
    parser.add_argument("-f", "--files", default=None, nargs="?", const=f_dump)
    parser.add_argument("-c", "--checksum", default=None, nargs="?", const=f_checksum)
    parser.add_argument("--files-key", default="/")
    parser.add_argument("--checksum-key", default="/")
    parser.add_argument("--ignore", action="store_true")
    parser.add_argument("-i", "--input", default=None, nargs="?", const=f_hostinfo)
    parser.add_argument("--remove", nargs="*")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=version)
    args = parser.parse_args()

    # Separate mode: remove paths and quit

    if args.remove:
        filename = args.output
        if args.input:
            filename = args.input
        data = yaml.read(filename)
        data = remove(data, args.remove)
        yaml.dump(args.output, data, args.force)
        return 0

    # Extract basic information from command-line arguments

    data = {}

    if args.host:
        data["host"] = args.host

    if args.prefix:
        data["prefix"] = args.prefix

    if args.input:
        overwrite = yaml.read(args.input)
        for item in ["host", "prefix"]:
            if item in overwrite:
                data[item] = overwrite[item]

    # Basic IO-checks

    if not args.ignore:
        if "host" in data and "prefix" not in data:
            raise OSError("Specify hostname and prefix")

    if "host" not in data and "prefix" not in data:
        for item in [args.files, args.checksum]:
            if item:
                data["prefix"] = os.path.dirname(item)
                break

    # Create temporary file to download to

    if "host" in data:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, f_hostinfo)

    # Read files and checksums

    args_dict = vars(args)

    for item in ["files", "checksum"]:

        if args_dict[item]:

            key = list(filter(None, args_dict[item + "_key"].split("/")))
            filename = args_dict[item]

            if "host" in data:
                scp.from_remote(
                    data["host"],
                    os.path.join(data["prefix"], filename),
                    temp_file,
                    args.verbose,
                )
                filename = temp_file

            data[item] = yaml.read_item(filename, key)

    # Run basic checks

    if not args.ignore:
        for item in ["prefix"]:
            if item not in data:
                raise OSError(f"Please specify {item:s}")
        if "checksum" in data:
            if len(data["files"]) != len(data["checksum"]):
                raise OSError("Number of checksums does not match number of files")

    # Clean-up: remove temporary file

    if "host" in data:
        shutil.rmtree(temp_dir)

    # Write output

    if "files" not in data:
        data["files"] = []

    yaml.dump(args.output, data, args.force)


def main():

    try:
        main_impl()
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":

    main()
