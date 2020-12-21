import unittest
import subprocess
import os
import shutil
from shelephant.cli import YamlGetItem
from shelephant.cli import YamlRead
from shelephant.cli import YamlDump


def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


class Test_checksum(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump foo.txt bar.txt')
        output = run('shelephant_checksum shelephant_dump.yaml')
        data = YamlGetItem('shelephant_checksum.yaml')

        keys = [
            '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae',
            'fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9',
        ]

        self.assertEqual(data, keys)

        os.remove('foo.txt')
        os.remove('bar.txt')
        os.remove('shelephant_dump.yaml')
        os.remove('shelephant_checksum.yaml')


class Test_dump(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        os.mkdir('mydir')

        with open('mydir/foo.txt', 'w') as file:
            file.write('foo')

        with open('mydir/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -s -o dump_1.yaml foo.txt bar.txt')
        output = run('shelephant_dump -s -o dump_2.yaml *.txt')
        output = run('shelephant_dump -s -o mydir/dump_3.yaml mydir/*.txt')

        with open('dump_1.yaml', 'r') as file:
            dump_1 = file.read()

        with open('dump_2.yaml', 'r') as file:
            dump_2 = file.read()

        with open('mydir/dump_3.yaml', 'r') as file:
            dump_3 = file.read()

        self.assertEqual(dump_1, dump_2)
        self.assertEqual(dump_1, dump_3)

        os.remove('foo.txt')
        os.remove('bar.txt')
        os.remove('dump_1.yaml')
        os.remove('dump_2.yaml')
        shutil.rmtree('mydir')


class Test_extract(unittest.TestCase):

    def test_single_path(self):

        data = {
            'foo' : ['foo.txt', 'bar.txt'],
            'bar' : ['foo.pdf', 'bar.pdf'],
            'key' : ['foo.key', 'bar.key'],
        }

        YamlDump('dump.yaml', data, force=True)

        output = run('shelephant_extract --force dump.yaml "foo"')

        self.assertEqual(YamlRead('dump.yaml'), ['foo.txt', 'bar.txt'])

        os.remove('dump.yaml')

    def test_multiple_paths(self):

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

        self.assertEqual(YamlRead('dump.yaml'), {'foo': ['foo.txt', 'bar.txt'], 'sub': {'foo': ['foo.txt', 'bar.txt']}})

        os.remove('dump.yaml')


class Test_merge(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -o main.yaml foo.txt')
        output = run('shelephant_dump -o branch.yaml bar.txt')
        output = run('shelephant_merge --force branch.yaml main.yaml')

        self.assertEqual(YamlRead('main.yaml'), ['foo.txt', 'bar.txt'])

        os.remove('foo.txt')
        os.remove('bar.txt')
        os.remove('main.yaml')
        os.remove('branch.yaml')

        os.mkdir('dira')
        os.mkdir('dirb')

        with open('dira/foo.txt', 'w') as file:
            file.write('foo')

        with open('dira/bar.txt', 'w') as file:
            file.write('bar')

        with open('dirb/foo.txt', 'w') as file:
            file.write('foo')

        with open('dirb/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -o dira/dump.yaml dira/foo.txt dira/bar.txt')
        output = run('shelephant_dump -o dirb/dump.yaml dirb/foo.txt dirb/bar.txt')
        output = run('shelephant_merge --force dira/dump.yaml dirb/dump.yaml')

        self.assertEqual(YamlRead('dirb/dump.yaml'), ['foo.txt', 'bar.txt', '../dira/foo.txt', '../dira/bar.txt'])

        shutil.rmtree('dira')
        shutil.rmtree('dirb')


class Test_remote(unittest.TestCase):

    def test_basic(self):

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_remote -o mydest/remote.yaml --files mysrc/files.yaml --checksum mysrc/checksum.yaml')
        output = run('shelephant_get --force mydest/remote.yaml')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -o mydest/checksum.yaml mydest/files.yaml')

        with open('mysrc/files.yaml', 'r') as file:
            src_files = file.read()

        with open('mysrc/checksum.yaml', 'r') as file:
            src_checksum = file.read()

        with open('mydest/files.yaml', 'r') as file:
            dest_files = file.read()

        with open('mydest/checksum.yaml', 'r') as file:
            dest_checksum = file.read()

        self.assertEqual(src_files, dest_files)
        self.assertEqual(src_checksum, dest_checksum)

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')


class Test_rm(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump foo.txt bar.txt')
        output = run('shelephant_rm --force shelephant_dump.yaml')

        self.assertFalse(os.path.isfile('foo.txt'))
        self.assertFalse(os.path.isfile('bar.txt'))

        os.remove('shelephant_dump.yaml')


class Test_parse(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump foo.txt bar.txt')
        output = run('shelephant_parse shelephant_dump.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), ['- foo.txt', '- bar.txt'])

        os.remove('shelephant_dump.yaml')
        os.remove('foo.txt')
        os.remove('bar.txt')


if __name__ == '__main__':

    unittest.main()
