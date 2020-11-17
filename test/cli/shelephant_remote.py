import subprocess
import os
import shutil

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

os.mkdir('mysrc')
os.mkdir('mydest')
open('mysrc/foo.txt', 'w').write('foo')
open('mysrc/bar.txt', 'w').write('bar')

output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
output = run('shelephant_checksum -o mysrc/checksum.yaml mysrc/files.yaml')
output = run('shelephant_remote -o mydest/remote.yaml --files mysrc/files.yaml --checksum mysrc/checksum.yaml')
output = run('shelephant_get --force mydest/remote.yaml')
output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
output = run('shelephant_checksum -o mydest/checksum.yaml mydest/files.yaml')

assert open('mysrc/files.yaml', 'r').read() == open('mydest/files.yaml', 'r').read()
assert open('mysrc/checksum.yaml', 'r').read() == open('mydest/checksum.yaml', 'r').read()

shutil.rmtree('mysrc')
shutil.rmtree('mydest')
