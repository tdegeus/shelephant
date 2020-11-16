'''shelephant_remote
    Collect information from remote location (or host).

Usage:
    shelephant_remote [options]

Options:
    -o, --output=N          Output YAML-file. [default: shelephant_remote.yaml]
        --force             Force overwrite of output file.
        --host=N            Host-name.
        --prefix=N          Directory on remote, from which to copy.
    -f, --files=N           Read files from remote.
    -c, --checksum=N        Read checksums from remote.
        --files-key=N       Path in the YAML-file, separated by "/". [default: /]
        --checksum-key=N    Path in the YAML-file, separated by "/". [default: /]
    -i, --ignore            Skip basic check.
        --verbose           Verbose all commands.
    -h, --help              Show help.
        --version           Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os
import sys
import tempfile
import shutil

from .. import __version__
from . import Error
from . import GetList
from . import ReadYaml
from . import YamlDump
from . import ExecCommand
from . import CopyFromRemote


def main():

    args = docopt.docopt(__doc__, version=__version__)

    # Extract basic information from command-line arguments

    data = {}

    for item in ['host', 'prefix']:
        if args['--' + item]:
            data[item] = args['--' + item]

    # Basic IO-checks

    if not args['--ignore']:
        if 'host' in data and 'prefix' not in data:
            Error('Specify hostname and prefix')

    if 'host' not in data and 'prefix' not in data:
        for item in ['files', 'checksum']:
            if args['--' + item]:
                data['prefix'] = os.path.dirname(args['--' + item])
                break

    # Create temporary file to download to

    if 'host' in data:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'shelephant_remote.yaml')

    # Read files and checksums

    for item in ['files', 'checksum']:

        if args['--' + item]:

            key = list(filter(None, args['--' + item + '-key'].split('/')))
            filename = args['--' + item]

            if 'host' in data:
                CopyFromRemote(
                    data['host'],
                    os.path.join(data['prefix'], filename),
                    temp_file,
                    args['--verbose'])
                filename = temp_file

            data[item] = GetList(filename, key)

    # Run basic checks

    if not args['--ignore']:
        for item in ['prefix', 'files']:
            if item not in data:
                Error('Please specify {0:s}'.format(item))
        if 'checksum' in data:
            if len(data['files']) != len(data['checksum']):
                Error('Number of checksums does not match number of files')

    # Clean-up: remove temporary file

    if 'host' in data:
        shutil.rmtree(temp_dir)

    # Write output

    YamlDump(args['--output'], data, args['--force'])


if __name__ == '__main__':

    main()
