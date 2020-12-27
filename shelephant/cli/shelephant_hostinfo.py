'''shelephant_hostinfo
    Collect file information from location (on a remote host).

Usage:
    shelephant_hostinfo [options]

Options:
    -o, --output=N          Output YAML-file. [default: shelephant_hostinfo.yaml].
    -r, --host=N            Host-name.
    -p, --prefix=N          Directory (on host) from which to copy.
    -f, --files=[N]         YAML-file with list of files (on remote). [default: shelephant_dump.yaml]
    -c, --checksum=[N]      YAML-file with checksums (on remote). [default: shelephant_checksum.yaml]
        --files-key=N       Path in the YAML-file, separated by "/". [default: /]
        --checksum-key=N    Path in the YAML-file, separated by "/". [default: /]
    -i, --ignore            Skip basic checks.
    -u, --update=[N]        Use host and prefix from existing file. [default: shelephant_hostinfo.yaml]
        --force             Overwrite output file without prompt.
        --verbose           Verbose all commands.
    -h, --help              Show help.
        --version           Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import argparse
import os
import tempfile
import shutil

from .. import __version__
from .. import Error
from .. import YamlGetItem
from .. import YamlDump
from .. import YamlRead
from .. import CopyFromRemote


def main():

    # Parse command-line arguments

    class Parser(argparse.ArgumentParser):

        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument('-o', '--output', required=False, default='shelephant_hostinfo.yaml')
    parser.add_argument(      '--force', required=False, action='store_true')
    parser.add_argument(      '--host', required=False, default=None)
    parser.add_argument('-p', '--prefix', required=False, default=None)
    parser.add_argument('-f', '--files', required=False, default=None, nargs='?', const='shelephant_dump.yaml')
    parser.add_argument('-c', '--checksum', required=False, default=None, nargs='?', const='shelephant_checksum.yaml')
    parser.add_argument('-u', '--update', required=False, default=None, nargs='?', const='shelephant_hostinfo.yaml')
    parser.add_argument(      '--files-key', required=False, default='/')
    parser.add_argument(      '--checksum-key', required=False, default='/')
    parser.add_argument('-i', '--ignore', required=False, action='store_true')
    parser.add_argument(      '--verbose', required=False, action='store_true')
    parser.add_argument('-v', '--version', action='version', version=__version__)

    p = parser.parse_args()

    args = {
        '--output' : p.output,
        '--force' : p.force,
        '--host' : p.host,
        '--prefix' : p.prefix,
        '--files' : p.files,
        '--checksum' : p.checksum,
        '--update' : p.update,
        '--files-key' : p.files_key,
        '--checksum-key' : p.checksum_key,
        '--ignore' : p.ignore,
        '--verbose' : p.verbose,
    }

    # Extract basic information from command-line arguments

    data = {}

    for item in ['host', 'prefix']:
        if args['--' + item]:
            data[item] = args['--' + item]

    if args['--update']:
        overwrite = YamlRead(args['--update'])
        for item in ['host', 'prefix']:
            if item in overwrite:
                data[item] = overwrite[item]

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
        temp_file = os.path.join(temp_dir, 'shelephant_hostinfo.yaml')

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

            data[item] = YamlGetItem(filename, key)

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
