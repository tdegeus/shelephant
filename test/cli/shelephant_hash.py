import subprocess
import os
from shelephant.cli import GetList

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

open('foo.txt', 'w').write('foo')
open('bar.txt', 'w').write('bar')

output = run('shelephant_dump foo.txt bar.txt')
output = run('shelephant_checksum shelephant_dump.yaml')
data = GetList('shelephant_checksum.yaml')

keys = [
    '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae',
    'fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9',
]

assert data == keys

os.remove('foo.txt')
os.remove('bar.txt')
os.remove('shelephant_dump.yaml')
os.remove('shelephant_checksum.yaml')
