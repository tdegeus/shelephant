'''ssh_test
    Run SSH test.

Usage:
    ssh_test [options] --host=N --prefix=N

Options:
    -r, --host=N        Host name.
    -p, --prefix=M      Path on host.
        --version       Print version.
    -g, --help          Print this help.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

import subprocess
import docopt
import os

from shelephant import __version__
from shelephant import YamlGetItem
from shelephant import YamlRead
from shelephant import YamlDump


def run(cmd):
    print(cmd)
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


args = docopt.docopt(__doc__, version=__version__)

# shelephant_send - basic

operations = [
    'bar.txt -> bar.txt',
    'foo.txt == foo.txt',
    'bar.txt',
]

output = run(('shelephant_hostinfo -o myssh_send/shelephant_hostinfo.yaml --force '
              '--host "{0:s}" --prefix "{1:s}" -f -c').format(
    args['--host'], os.path.join(args['--prefix'], 'myssh_get')))

output = run(('shelephant_send --colors none --force '
              'myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml'))

output = output.split('\n')
output = output[6:-1]
output[-1] = output[-1].split(') ')[1]
assert output == operations

# shelephant_send - local checksum

operations = [
    'bar.txt -> bar.txt',
    'foo.txt == foo.txt',
    'bar.txt',
]

output = run(('shelephant_hostinfo -o myssh_send/shelephant_hostinfo.yaml --force '
              '--host "{0:s}" --prefix "{1:s}" -f -c').format(
              args['--host'], os.path.join(args['--prefix'], 'myssh_get')))

output = run(('shelephant_hostinfo -o myssh_send/shelephant_local.yaml --force '
              '-f myssh_send/shelephant_dump.yaml -c myssh_send/shelephant_checksum.yaml'))

output = run(('shelephant_send --colors none --force '
              'myssh_send/shelephant_dump.yaml myssh_send/shelephant_hostinfo.yaml'))

output = output.split('\n')
output = output[6:-1]
output[-1] = output[-1].split(') ')[1]
assert output == operations

# shelephant_get - basic

operations = [
    'bar.txt -> bar.txt',
    'foo.txt == foo.txt',
    'bar.txt',
]

output = run(('shelephant_hostinfo -o myssh_get/shelephant_hostinfo.yaml --force '
              '--host "{0:s}" --prefix "{1:s}" -f -c').format(
              args['--host'], os.path.join(args['--prefix'], 'myssh_send')))

output = run('shelephant_get --colors none --force myssh_get/shelephant_hostinfo.yaml')

output = output.split('\n')
output = output[6:-1]
output[-1] = output[-1].split(') ')[1]
assert output == operations

os.remove('myssh_get/bar.txt')
