'''shelephant_remote
    Collect information from remote location (or host).

Usage:
    shelephant_remote [options]

Options:
    -o, --output=N      Output YAML-file. [default: selephant_remote.yaml]
    -f, --force         Force overwrite of output file.
        --host=N        Host-name.
        --prefix=N      Directory on remote, from which to copy.
        --files=N       Filename of the YAML-file with files to copy, relative to --prefix.
        --hash=N        Filename of the YAML-file with the checksums of files, relative to --prefix.
        --files-path=N  Path where files are stored in the YAML-file, separated by "/". [default: /]
        --hash-path=N   Path where checksums are stored in the YAML-file, separated by "/". [default: /]
    -i, --ignore        Skip basic check.
        --verbose       Verbose all commands.
    -h, --help          Show help.
        --version       Show version.

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


def main():

    args = docopt.docopt(__doc__, version=__version__)
    data = {}

    for key in ['host', 'prefix']:
        if args['--' + key]:
            data[key] = args['--' + key]

    if not args['--ignore']:
        if 'host' in data and 'prefix' not in data:
            Error('Specify hostname and prefix')

    if 'host' not in data and 'prefix' not in data:
        for key in ['files', 'hash']:
            if args['--' + key]:
                data['prefix'] = os.path.dirname(args['--' + key])
                break

    if 'host' in data:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'shelephant_remote.yaml')

    for key in ['files', 'hash']:
        if args['--' + key]:

            path = list(filter(None, args['--' + key + '-path'].split('/')))
            filename = args['--' + key]

            if 'host' in data:
                cmd = 'scp {host:s}:{prefix:s}/{filename:s} {tempname:s}'.format(
                    **data, filename=filename, tempname=temp_file)
                ExecCommand(cmd, args['--verbose'])
                filename = temp_file

            data[key] = GetList(filename, path)

    if not args['--ignore']:
        for key in ['prefix', 'files']:
            if key not in data:
                Error('Please specify {0:s}'.format(key))
        if 'hash' in data:
            if len(data['files']) != len(data['hash']):
                Error('Number of checksums does not match number of files')

    if 'host' in data:
        shutil.rmtree(temp_dir)

    if args['--append']:
        filename = args['--append']
    else:
        filename = args['--output']
    YamlDump(filename, data, args['--force'])


if __name__ == '__main__':

    main()
