import subprocess
import os
import shutil

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

open('foo.txt', 'w').write('foo')
open('bar.txt', 'w').write('bar')
os.mkdir('tmp')
open('tmp/foo.txt', 'w').write('foo')
open('tmp/bar.txt', 'w').write('bar')

output = run('shelephant_dump -s -o dump_1.yaml -f foo.txt bar.txt')
output = run('shelephant_dump -s -o dump_2.yaml -f *.txt')
output = run('shelephant_dump -s -o tmp/dump_3.yaml -f tmp/*.txt')

assert open('dump_1.yaml', 'r').read() == open('dump_2.yaml', 'r').read()
assert open('dump_1.yaml', 'r').read() == open('tmp/dump_3.yaml', 'r').read()

os.remove('foo.txt')
os.remove('bar.txt')
os.remove('dump_1.yaml')
os.remove('dump_2.yaml')
shutil.rmtree('mydir')
