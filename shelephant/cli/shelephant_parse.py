'''shelephant_parse
    Parse a YAML-file, and print to screen.

Usage:
    shelephant_parse <file.yaml>

Argument:
    File path.

Options:
    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt

from .. import version
from .. import YamlRead
from .. import YamlPrint


def main():

    try:

        args = docopt.docopt(__doc__, version=version)
        source = args['<file.yaml>']
        data = YamlRead(source)
        YamlPrint(data)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
