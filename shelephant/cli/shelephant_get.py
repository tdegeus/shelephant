'''shelephant_get
    Copy files using earlier collected information on which files to copy from where.

Usage:
    shelephant_get [options]
    shelephant_get [options] <hostinfo.yaml>

Argument:
    YAML-file with host information. Default: shelephant_hostinfo.yaml

Options:
        --colors=M  Select color scheme from: none, dark. [default: dark]
    -q, --quiet     Do not print progress.
    -f, --force     Force overwrite of all existing (but not matching) files.
    -l, --local=N   Add local 'host' information to use precomputed checksums.
    -s, --summary   Print summary (and no details unless specified).
    -d, --details   Print details (and no summary unless specified).
        --verbose   Verbose all commands.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os
import shutil
import math

from .. import __version__
from .. import YamlRead
from .. import CopyFromRemote
from .. import ShelephantCopy
from .. import ShelephantCopySSH


def main():

    args = docopt.docopt(__doc__, version=__version__)
    source = args['<hostinfo.yaml>'] if args['<hostinfo.yaml>'] else 'shelephant_hostinfo.yaml'
    data = YamlRead(source)

    if 'host' not in data:

        ShelephantCopy(
            copy_function = shutil.copy,
            files = data['files'],
            src_dir = data['prefix'],
            dest_dir = os.path.dirname(source),
            checksum = 'checksum' in data,
            quiet = args['--quiet'],
            force = args['--force'],
            print_details = not (args['--force'] or args['--summary']) or args['--details'],
            print_summary = not (args['--force'] or args['--details']) or args['--summary'],
            print_all = args['--details'],
            theme_name = args['--colors'].lower(),
            yaml_hostinfo_src = source,
            yaml_hostinfo_dest = args['--local'])

    else:

        ShelephantCopySSH(
            copy_function = CopyFromRemote,
            host = data['host'],
            files = data['files'],
            src_dir = data['prefix'],
            dest_dir = os.path.dirname(source),
            checksum = 'checksum' in data,
            quiet = args['--quiet'],
            force = args['--force'],
            print_details = not (args['--force'] or args['--summary']) or args['--details'],
            print_summary = not (args['--force'] or args['--details']) or args['--summary'],
            print_all = args['--details'],
            verbose = args['--verbose'],
            theme_name = args['--colors'].lower(),
            yaml_hostinfo_src = source,
            yaml_hostinfo_dest = args['--local'])


if __name__ == '__main__':

    main()
