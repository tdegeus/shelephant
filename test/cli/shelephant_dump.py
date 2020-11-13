import subprocess
import os
import shutil

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

open('foo.txt', 'w').write('foo')
open('bar.txt', 'w').write('bar')
os.mkdir('mydir')
open('mydir/foo.txt', 'w').write('foo')
open('mydir/bar.txt', 'w').write('bar')

output = run('shelephant_dump -s -o dump_1.yaml -f foo.txt bar.txt')
output = run('shelephant_dump -s -o dump_2.yaml -f *.txt')
output = run('shelephant_dump -s -o mydir/dump_3.yaml -f mydir/*.txt')

assert open('dump_1.yaml', 'r').read() == open('dump_2.yaml', 'r').read()
assert open('dump_1.yaml', 'r').read() == open('mydir/dump_3.yaml', 'r').read()

os.remove('foo.txt')
os.remove('bar.txt')
os.remove('dump_1.yaml')
os.remove('dump_2.yaml')
shutil.rmtree('mydir')
