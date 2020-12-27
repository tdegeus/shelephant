'''shelephant_parse
    Parse a YAML-file, and print to screen.

Usage:
    shelephant_parse <file.yaml>

Argument:
    File path.

Options:
    -h, --help          Show help.
        --version       Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import docopt

from .. import __version__
from .. import YamlRead
from .. import YamlPrint


def main():

    args = docopt.docopt(__doc__, version=__version__)
    source = args['<file.yaml>']
    data = YamlRead(source)
    YamlPrint(data)


if __name__ == '__main__':

    main()
