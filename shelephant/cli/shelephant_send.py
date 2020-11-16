'''shelephant_send
    Copy files to a remote.

Usage:
    shelephant_get [options] <files.yaml> <remote.yaml>

Options:
    -k, --key=N         Path where files are stored in the YAML-file, separated by "/". [default: /]
    -f, --force         Force overwrite of all existing (but not matching) files.
        --colors=M      Select color scheme from: none, dark. [default: dark]
        --verbose       Verbose all commands.
    -q, --quiet         Do not print progress.
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt
import click
import os
import sys
import shutil
import math
import numpy as np

from .. import __version__
from . import ReadYaml
from . import ExecCommand
from . import PrefixPaths
from . import GetList
from . import GetSHA256
from . import Theme
from . import String


def main():

    args = docopt.docopt(__doc__, version=__version__)
    data = ReadYaml(args['<remote.yaml>'])
    key = list(filter(None, args['--key'].split('/')))
    files = GetList(args['<files.yaml>'], key)
    src_dir = os.path.dirname(args['<files.yaml>'])
    dest_dir = data['prefix']
    src = PrefixPaths(src_dir, files)
    dest = PrefixPaths(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    theme = Theme(args['--colors'].lower())

    if 'files' in data:

        if len(set(data['files'])) != len(data['files']):
            Error('files in remote must be unique')

        for i in range(n):
            if files[i] in data['files']:
                if 'checksum' in data:
                    j = np.argwhere([file == files[i] for file in data['files']]).ravel()[0]
                    if GetSHA256(src[i]) == data['checksum'][j]:
                        skip[i] = True
                        continue
                overwrite[i] = True
                continue
            create[i] = True

    print('-----')
    if 'host' in data:
        print('- to host           : ' + data['host'])
        print('- from dir. (local) : ' + os.path.normpath(src_dir))
        print('- to dir. (remote)  : ' + os.path.normpath(dest_dir))
    else:
        print('- from dir. : ' + os.path.normpath(src_dir))
        print('- to dir.   : ' + os.path.normpath(dest_dir))
    print('-----')

    l = max([len(file) for file in files])

    for i in range(n):
        if create[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['bright']).format(),
                String('->', color=theme['bright']).format(),
                String(files[i], color=theme['new']).format()
            ))
        elif skip[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['skip']).format(),
                String('==', color=theme['skip']).format(),
                String(files[i], color=theme['skip']).format()
            ))
        elif overwrite[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['bright']).format(),
                String('=>', color=theme['bright']).format(),
                String(files[i], color=theme['overwrite']).format()
            ))

    if all(skip):
        return 0

    if not args['--force']:
        if not click.confirm('Proceed?'):
            return 1

    ncp = n - sum(skip)
    l = int(math.log10(ncp) + 1)
    fmt = '({0:' + str(l) + 'd}/' + ('{0:' + str(l) + 'd}').format(ncp) + ') {1:s}'

    for i in range(n):
        if not skip[i]:
            if not args['--quiet']:
                print(fmt.format(i, dest[i]))
            if 'host' in data:
                ExecCommand(
                    'scp {0:s} {1:s}:{2:s}'.format(src[i], data['host'], dest[i]),
                    args['--verbose'])
            else:
                shutil.copy(src[i], dest[i])


if __name__ == '__main__':

    main()
