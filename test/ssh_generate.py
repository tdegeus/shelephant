import os
import shutil
import subprocess


def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


for dirname in ['myssh_send', 'myssh_get']:

    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

    os.mkdir(dirname)

with open('myssh_send/bar.txt', 'w') as file:
    file.write('bar')

with open('myssh_send/foo.txt', 'w') as file:
    file.write('foo')

with open('myssh_get/foo.txt', 'w') as file:
    file.write('foo')

output = run('shelephant_dump -o myssh_send/shelephant_dump.yaml myssh_send/bar.txt myssh_send/foo.txt')
output = run('shelephant_dump -o myssh_get/shelephant_dump.yaml myssh_get/foo.txt')
output = run('shelephant_checksum -o myssh_send/shelephant_checksum.yaml myssh_send/shelephant_dump.yaml')
output = run('shelephant_checksum -o myssh_get/shelephant_checksum.yaml myssh_get/shelephant_dump.yaml')


