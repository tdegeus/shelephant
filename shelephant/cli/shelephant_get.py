'''shelephant_get
    Copy files using earlier collected information on which files to copy from where.

Usage:
    shelephant_get [options] <remote.yaml>

Options:
        --colors=M      Select color scheme from: none, dark. [default: dark]
    -q, --quiet         Do not print progress.
    -f, --force         Force overwrite of all existing (but not matching) files.
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

from .. import __version__
from . import YamlRead
from . import PrefixPaths
from . import GetSHA256
from . import Theme
from . import String
from . import CopyFromRemote


def main():

    args = docopt.docopt(__doc__, version=__version__)
    data = YamlRead(args['<remote.yaml>'])
    files = data['files']
    src_dir = data['prefix']
    dest_dir = os.path.dirname(args['<remote.yaml>'])
    src = PrefixPaths(src_dir, files)
    dest = PrefixPaths(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    theme = Theme(args['--colors'].lower())

    for i in range(n):
        if os.path.isfile(dest[i]):
            if 'checksum' in data:
                if GetSHA256(dest[i]) == data['checksum'][i]:
                    skip[i] = True
                    continue
            overwrite[i] = True
            continue
        create[i] = True

    print('-----')
    if 'host' in data:
        print('- from host          : ' + data['host'])
        print('- from dir. (remote) : ' + os.path.normpath(src_dir))
        print('- to dir. (local)    : ' + os.path.normpath(dest_dir))
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
                CopyFromRemote(data['host'], src[i], dest[i], args['--verbose'])
            else:
                shutil.copy(src[i], dest[i])


if __name__ == '__main__':

    main()
