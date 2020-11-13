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
output = run('shelephant_hash -o mysrc/hash.yaml mysrc/files.yaml')
output = run('shelephant_remote -f -o mydest/remote.yaml --files mysrc/files.yaml --hash mysrc/hash.yaml')
output = run('shelephant_get -f mydest/remote.yaml')
output = run('shelephant_dump -s -f -o mydest/files.yaml mydest/*.txt')
output = run('shelephant_hash -o mydest/hash.yaml mydest/files.yaml')

assert open('mysrc/files.yaml', 'r').read() == open('mydest/files.yaml', 'r').read()
assert open('mysrc/hash.yaml', 'r').read() == open('mydest/hash.yaml', 'r').read()

shutil.rmtree('mysrc')
shutil.rmtree('mydest')
