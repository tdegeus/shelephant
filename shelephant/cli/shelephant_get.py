'''shelephant_get
    Copy files.

Usage:
    shelephant_get [options] <remote.yaml>

Options:
    -f, --force         Force overwrite of output file.
        --colors=M      Select color scheme from: none, dark. [default: dark]
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
from . import PrefixPaths
from . import GetSHA256
from . import Theme
from . import String


def strike(text):
    return ''.join([u'\u0336{}'.format(c) for c in text])


def main():

    args = docopt.docopt(__doc__, version=__version__)
    data = ReadYaml(args['<remote.yaml>'])
    dest = PrefixPaths(os.path.dirname(args['<remote.yaml>']), data['files'])
    n = len(dest)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    src = PrefixPaths(data['prefix'], data['files'])
    theme = Theme(args['--colors'].lower())

    for i in range(n):
        if os.path.isfile(dest[i]):
            if 'hash' in data:
                if GetSHA256(dest[i]) == data['hash'][i]:
                    skip[i] = True
                    continue
            overwrite[i] = True
            continue
        create[i] = True

    # local copy

    if 'host' not in data:

        l = max([len(file) for file in src])

        for i in range(n):
            if create[i]:
                print('{0:s} {1:s} {2:s}'.format(
                    String(src[i], width=l, color=theme['new']).format(),
                    String('->', color=theme['new']).format(),
                    String(dest[i]).format()
                ))
            elif skip[i]:
                print('{0:s} {1:s} {2:s}'.format(
                    String(src[i], width=l, color=theme['skip']).format(),
                    String('==', color=theme['skip']).format(),
                    String(dest[i], color=theme['skip']).format()
                ))
            elif overwrite[i]:
                print('{0:s} {1:s} {2:s}'.format(
                    String(src[i], width=l, color=theme['new']).format(),
                    String('->', color=theme['new']).format(),
                    String(dest[i], color=theme['overwrite']).format()
                ))

        if all(skip):
            return 0

        if not args['--force']:
            if not click.confirm('Proceed?'):
                return 1

        for i in range(n):
            if not skip[i]:
                shutil.copy(src[i], dest[i])

        return 0

    # remote copy

    l = max([len(file) + len(data['host'] + ':') for file in src])

    for i in range(n):
        if create[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(data['host'] + ':' + src[i], width=l, color=theme['new']).format(),
                String('->', color=theme['new']).format(),
                String(dest[i]).format()
            ))
        elif skip[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(data['host'] + ':' + src[i], width=l, color=theme['skip']).format(),
                String('==', color=theme['skip']).format(),
                String(dest[i], color=theme['skip']).format()
            ))
        elif overwrite[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(data['host'] + ':' + src[i], width=l, color=theme['new']).format(),
                String('->', color=theme['new']).format(),
                String(dest[i], color=theme['overwrite']).format()
            ))

    if all(skip):
        return 0

    if not args['--force']:
        if not click.confirm('Proceed?'):
            return 1

    for i in range(n):
        if not skip[i]:
            ExecCommand('scp {0:s}:{1:s} {2:s}'.format(data['host'], src[i], dest[i]), args['--verbose'])

    return 0


if __name__ == '__main__':

    main()
