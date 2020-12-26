'''shelephant_send
    Copy files to a remote, using earlier collected information on which files to copy where.

Usage:
    shelephant_send [options]
    shelephant_send [options] <files.yaml> <remote.yaml>

Arguments:
    files.yaml          YAML-file with files to send. Default: shelephant_dump.yaml
    remote.yaml         YAML-file with host information. Default: shelephant_remote.yaml

Options:
    -k, --key=N         Path in the YAML-file, separated by "/". [default: /]
        --colors=M      Select color scheme from: none, dark. [default: dark]
    -q, --quiet         Do not print progress.
    -f, --force         Force overwrite of all existing (but not matching) files.
    -l, --local=N       Add local 'host' information to use precomputed checksums.
        --verbose       Verbose all commands.
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os
import shutil
import math
import numpy as np

from .. import __version__
from . import YamlRead
from . import PrefixPaths
from . import YamlGetItem
from . import GetSHA256
from . import Theme
from . import String
from . import CopyToRemote
from . import ShelephantCopy
from . import ShelephantCopySSH


def ReadChecksums(shelephant_remote, dest):

    import numpy as np

    data = YamlRead(shelephant_remote)
    files = data['files']
    prefix = data['prefix']
    checksum = data['checksum']
    paths = PrefixPaths(prefix, files)

    n = len(dest)
    ret = [False for i in range(n)]

    for i in range(n):
        if os.path.isfile(dest[i]):
            j = np.argwhere([file == dest[i] for file in paths]).ravel()[0]
            ret[i] = checksum[j]

    return ret


def ComputeChecksums(dest):

    n = len(dest)
    ret = [False for i in range(n)]

    for i in range(n):
        if os.path.isfile(dest[i]):
            ret[i] = GetSHA256(dest[i])

    return ret


def main():

    args = docopt.docopt(__doc__, version=__version__)
    source = args['<files.yaml>'] if args['<files.yaml>'] else 'shelephant_dump.yaml'
    remote = args['<remote.yaml>'] if args['<remote.yaml>'] else 'shelephant_remote.yaml'
    data = YamlRead(remote)
    key = list(filter(None, args['--key'].split('/')))
    files = YamlGetItem(source, key)
    src_dir = os.path.dirname(source)
    dest_dir = data['prefix']

    if 'host' not in data:

        ShelephantCopy(
            copy_function = shutil.copy,
            yaml_src = source,
            yaml_key = key,
            dest_dir = data['prefix'],
            checksum = 'checksum' in data,
            quiet = args['--quiet'],
            force = args['--force'],
            theme_name = args['--colors'].lower(),
            yaml_hostinfo_src = args['--local'],
            yaml_hostinfo_dest = remote)

    else:

        ShelephantCopySSH(
            copy_function = CopyToRemote,
            host = data['host'],
            files = files,
            src_dir = src_dir,
            dest_dir = dest_dir,
            checksum = 'checksum' in data,
            quiet = args['--quiet'],
            force = args['--force'],
            verbose = args['--verbose'],
            theme_name = args['--colors'].lower(),
            yaml_hostinfo_src = args['--local'],
            yaml_hostinfo_dest = remote)


if __name__ == '__main__':

    main()
