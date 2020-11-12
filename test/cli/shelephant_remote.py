import subprocess
import os
import shutil

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

os.mkdir('mysrc')
os.mkdir('mydest')
open('mysrc/foo.txt', 'w').write('foo')
open('mysrc/bar.txt', 'w').write('bar')

output = run('shelephant_dump -s -f -o mysrc/files.yaml mysrc/*.txt')
output = run('shelephant_hash -s -f -o mysrc/hash.yaml mysrc/files.yaml')
output = run('shelephant_remote -f -o mydest/remote.yaml --files mysrc/files.yaml --hash mysrc/hash.yaml')

assert open('dump_1.yaml', 'r').read() == open('dump_2.yaml', 'r').read()
assert open('dump_1.yaml', 'r').read() == open('mysrc/dump_3.yaml', 'r').read()

shutil.rmtree('mysrc')
shutil.rmtree('mydest')
