import subprocess
import os
import shutil
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

os.mkdir('dira')
open('dira/foo.txt', 'w').write('foo')
open('dira/bar.txt', 'w').write('bar')

os.mkdir('dirb')
open('dirb/foo.txt', 'w').write('foo')
open('dirb/bar.txt', 'w').write('bar')

output = run('shelephant_dump -o dira/dump.yaml dira/foo.txt dira/bar.txt')
output = run('shelephant_dump -o dirb/dump.yaml dirb/foo.txt dirb/bar.txt')
output = run('shelephant_merge --force dira/dump.yaml dirb/dump.yaml')

assert ReadYaml('dirb/dump.yaml') == ['foo.txt', 'bar.txt', '../dira/foo.txt', '../dira/bar.txt']

shutil.rmtree('dira')
shutil.rmtree('dirb')
