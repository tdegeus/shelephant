import subprocess
import os
import shutil
from shelephant.cli import ReadYaml
from shelephant.cli import YamlDump

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

# single path

data = {
    'foo' : ['foo.txt', 'bar.txt'],
    'bar' : ['foo.pdf', 'bar.pdf'],
    'key' : ['foo.key', 'bar.key'],
}

YamlDump('dump.yaml', data, force=True)

output = run('shelephant_extract --force dump.yaml "foo"')

assert ReadYaml('dump.yaml') == ['foo.txt', 'bar.txt']

os.remove('dump.yaml')

# multiple (nested) paths

data = {
    'foo' : ['foo.txt', 'bar.txt'],
    'bar' : ['foo.pdf', 'bar.pdf'],
    'key' : ['foo.key', 'bar.key'],
    'sub' : {
        'foo' : ['foo.txt', 'bar.txt'],
        'bar' : ['foo.pdf', 'bar.pdf'],
        'key' : ['foo.key', 'bar.key'],
    },
}

YamlDump('dump.yaml', data, force=True)

output = run('shelephant_extract --force dump.yaml "/sub/foo" "foo"')

assert ReadYaml('dump.yaml') == {'foo': ['foo.txt', 'bar.txt'], 'sub': {'foo': ['foo.txt', 'bar.txt']}}

os.remove('dump.yaml')
