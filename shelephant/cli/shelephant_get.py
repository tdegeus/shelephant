"""Copy files from remote, using earlier collected host-information.
Use ``shelephant_hostinfo`` to collect host-information.

By default, *rsync* is used to check if files are different.
*rsync* uses basic criteria such as file size and creation and modification date,
see `rsync manual <https://www.samba.org/ftp/rsync/rsync.html>`_.
This is fast but is only approximate.
In addition you can use:

*   ``--checksum``: Have *rsync* compare checksums of files.
*   ``--check-manual``: Do not use *rsync*.
    If ``--checksum`` is used, checksums are compared (that are optionally precomputed).

The default copy backend is ``rysnc -a --from-file="temp" host:source_dir dest_dir``.
Alternatively ``scp -p host:source_file dest_file`` can be used.
Typically, *rsync* will be faster, especially in copying a lot of small files.

:usage:

    shelephant_get [options]

    shelephant_get [options] <hostinfo.yaml>

:argument:

    YAML-file with host information. Default: shelephant_hostinfo.yaml

:options:

    -l, --local=arg
        Add local 'host' information to use precomputed checksums.

    --scp
        Use ``scp`` instead of ``rysnc`` as backend.

    -M, --check-manual
        Use internal algorithms instead of *rsync*.

    --colors=arg
        Select color scheme from: none, dark. [default: dark]

    -s, --summary
        Print summary (and no details unless specified).

    -d, --details
        Print details (and no summary unless specified).

    -f, --force
        Force overwrite of all existing (but not matching) files.

    --verbose
        Verbose all commands.

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
from .. import rsync
from .. import scp
from .. import version
from .. import yaml
from .defaults import f_hostinfo


def main_impl():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-l", "--local")
    parser.add_argument("--scp", action="store_true")
    parser.add_argument("-M", "--check-manual", action="store_true")
    parser.add_argument("--colors", default="dark")
    parser.add_argument("-s", "--summary", action="store_true")
    parser.add_argument("-d", "--details", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("hostinfo", nargs="?", default=f_hostinfo)
    args = parser.parse_args()

    use_rsync = True
    if args.check_manual:
        use_rsync = False
    if not shutil.which("rsync"):
        warnings.warn("rsync not found, using internal fallback")
        use_rsync = False

    source = args.hostinfo
    data = yaml.read(source)

    if "host" not in data:

        detail.copy(
            copy_function=shutil.copy2,
            files=data["files"],
            src_dir=data["prefix"],
            dest_dir=os.path.dirname(source),
            checksum="checksum" in data,
            check_rsync=use_rsync,
            quiet=args.quiet,
            force=args.force,
            print_details=not (args.force or args.summary) or args.details,
            print_summary=not (args.force or args.details) or args.summary,
            print_all=args.details,
            theme_name=args.colors.lower(),
            yaml_hostinfo_src=source,
            yaml_hostinfo_dest=args.local,
        )

    elif args.scp:

        detail.copy_ssh(
            copy_function=scp.from_remote,
            use_rsync=False,
            host=data["host"],
            files=data["files"],
            src_dir=data["prefix"],
            dest_dir=os.path.dirname(source),
            checksum="checksum" in data,
            to_remote=False,
            check_rsync=use_rsync,
            quiet=args.quiet,
            force=args.force,
            print_details=not (args.force or args.summary) or args.details,
            print_summary=not (args.force or args.details) or args.summary,
            print_all=args.details,
            verbose=args.verbose,
            theme_name=args.colors.lower(),
            yaml_hostinfo_src=source,
            yaml_hostinfo_dest=args.local,
        )

    else:

        detail.copy_ssh(
            copy_function=rsync.from_remote,
            use_rsync=True,
            host=data["host"],
            files=data["files"],
            src_dir=data["prefix"],
            dest_dir=os.path.dirname(source),
            checksum="checksum" in data,
            to_remote=False,
            check_rsync=use_rsync,
            quiet=args.quiet,
            force=args.force,
            print_details=not (args.force or args.summary) or args.details,
            print_summary=not (args.force or args.details) or args.summary,
            print_all=args.details,
            verbose=args.verbose,
            theme_name=args.colors.lower(),
            yaml_hostinfo_src=source,
            yaml_hostinfo_dest=args.local,
        )


def main():

    try:
        main_impl()
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":

    main()
