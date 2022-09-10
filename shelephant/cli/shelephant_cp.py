"""Copy files listed in a (field of a) YAML-file.
The filenames are assumed either absolute, or relative to the input YAML-file.

By default, *rsync* is used to check if files are different.
*rsync* uses basic criteria such as file size and creation and modification date,
see `rsync manual <https://www.samba.org/ftp/rsync/rsync.html>`_.
This is fast but is only approximate.
In addition you can use:

*   ``--checksum``: Have *rsync* compare checksums of files.
*   ``--check-manual``: Do not use *rsync*.
    If ``--checksum`` is used, checksums are compared (that are optionally precomputed).

:usage:

    shelephant_cp [options] <destination>

    shelephant_cp [options] <input.yaml> <destination>

:arguments:

    <input.yaml>
        YAML-file with filenames. Default: shelephant_dump.yaml

    <destination>
        Prefix of the destination.

:options:

    -c, --checksum
        Use checksum to skip files that are the same.

    -M, --check-manual
        Use internal algorithms instead of *rsync*.

    -k, --key=arg
        Path in the YAML-file, separated by "/". [default: /]

    --colors=arg
        Select color scheme from: none, dark. [default: dark]

    -s, --summary
        Print summary (and no details unless specified).

    -d, --details
        Print details (and no summary unless specified).

    -f, --force
        Move without prompt.

    -q, --quiet
        Do not print progress.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
"""
import argparse
import os
import shutil
import warnings

from .. import detail
from .. import version
from .. import yaml


def main_impl():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-c", "--checksum", action="store_true")
    parser.add_argument("-M", "--check-manual", action="store_true")
    parser.add_argument("-k", "--key", default="/")
    parser.add_argument("--colors", default="dark")
    parser.add_argument("-s", "--summary", action="store_true")
    parser.add_argument("-d", "--details", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("args", nargs="+")
    args = parser.parse_args()

    use_rsync = True
    if args.check_manual:
        use_rsync = False
    if not shutil.which("rsync"):
        warnings.warn("rsync not found, using internal fallback")
        use_rsync = False

    if len(args.args) == 1:
        source = "shelephant_dump.yaml"
        dest_dir = args.args[0]
    elif len(args.args) == 2:
        source = args.args[0]
        dest_dir = args.args[1]
    else:
        raise OSError("Too many arguments specified")

    key = list(filter(None, args.key.split("/")))

    return detail.copy(
        copy_function=shutil.copy2,
        files=yaml.read_item(source, key),
        src_dir=os.path.dirname(source),
        dest_dir=dest_dir,
        checksum=args.checksum,
        check_rsync=use_rsync,
        quiet=args.quiet,
        force=args.force,
        print_details=not (args.force or args.summary) or args.details,
        print_summary=not (args.force or args.details) or args.summary,
        print_all=args.details,
        theme_name=args.colors.lower(),
    )


def main():

    try:
        main_impl()
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":

    main()
