import subprocess
import os

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

open('foo.txt', 'w').write('foo')
open('bar.txt', 'w').write('bar')

output = run('shelephant_dump foo.txt bar.txt')
output = run('shelephant_rm --force shelephant_dump.yaml')

assert not os.path.isfile('foo.txt')
assert not os.path.isfile('bar.txt')

os.remove('shelephant_dump.yaml')
