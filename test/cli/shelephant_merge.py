import subprocess
import os
from shelephant.cli import ReadYaml

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

open('foo.txt', 'w').write('foo')
open('bar.txt', 'w').write('bar')

output = run('shelephant_dump -o main.yaml foo.txt')
output = run('shelephant_dump -o branch.yaml bar.txt')
output = run('shelephant_merge --force branch.yaml main.yaml')

assert ReadYaml('main.yaml') == ['foo.txt', 'bar.txt']

os.remove('foo.txt')
os.remove('bar.txt')
os.remove('main.yaml')
os.remove('branch.yaml')
