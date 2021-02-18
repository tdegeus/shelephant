'''shelephant_parse
    Parse a YAML-file, and print to screen.

Usage:
    shelephant_parse [options]
    shelephant_parse [options] <file.yaml>

Argument:
    File path.

Options:
    -h, --help
        Show help.

    --version
        Show version.

    --git
        Print git branch and commit hash at the time this script was installed.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt

from .. import __version__
from .. import YamlRead
from .. import YamlPrint
from .. import git


def main():

    try:

        args = docopt.docopt(__doc__, version=__version__)

        if args['--git']:
            print(", ".join(git()))
            return 0

        if not args["<file>"]:
            print("A YAML-file is required as input")
            return 1

        source = args['<file.yaml>']
        data = YamlRead(source)
        YamlPrint(data)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
