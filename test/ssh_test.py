'''ssh_test
    Run SSH test.

Usage:
    ssh_test [options]

Options:
    -r, --host=N        Host name.
    -p, --prefix=M      Path on host.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import subprocess
import docopt
import os

from shelephant import __version__
from shelephant.cli import YamlGetItem
from shelephant.cli import YamlRead
from shelephant.cli import YamlDump


def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


args = docopt.docopt(__doc__, version=__version__)

# shelephant_send - basic

operations = [
    'bar.txt -> bar.txt',
    'foo.txt == foo.txt',
    'bar.txt',
]

output = run('shelephant_remote -o myssh_send/shelephant_remote.yaml --force --host "{0:s}" --prefix "{1:s}" -f -c'.format(
    args['--host'], os.path.join(args['--prefix'], 'myssh_get')))

output = run('shelephant_send --colors none --force myssh_send/shelephant_dump.yaml shelephant_remote.yaml')

output = output.split('\n')
output = output[5:-1]
output[-1] = output[-1].split(') ')[1]
assert output == operations

# shelephant_get - basic

operations = [
    'bar.txt -> bar.txt',
    'foo.txt == foo.txt',
    'bar.txt',
]

output = run('shelephant_remote -o myssh_get/shelephant_remote.yaml --force --host "{0:s}" --prefix "{1:s}" -f -c'.format(
    args['--host'], os.path.join(args['--prefix'], 'myssh_send')))

output = run('shelephant_get --colors none --force myssh_get/shelephant_remote.yaml')

output = output.split('\n')
output = output[5:-1]
output[-1] = output[-1].split(') ')[1]
assert output == operations
