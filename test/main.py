import unittest
import subprocess
import os
import shutil
import numpy as np

from shelephant import YamlGetItem
from shelephant import YamlRead
from shelephant import YamlDump
from shelephant import GetDeepestPaths


def run(cmd, verbose=False):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


class Test_tools(unittest.TestCase):

    def test_FlattenList(self):

        from shelephant import FlattenList

        arg = [1, [2, 2, 2], 4]
        ret = [1, 2, 2, 2, 4]

        self.assertEqual(ret, FlattenList(arg))

    def test_Squash(self):

        from shelephant import Squash

        arg = {'foo': [1, 2], 'bar': {'foo': [3, 4], 'bar': 5}}
        ret = [1, 2, 3, 4, 5]

        self.assertEqual(ret, Squash(arg))

    def test_deepest_dirs(self):

        dirnames = [
            "foo/bar",
            "foo/bar/mydir",
            "bar/mydir",
            "bar" ,
            "bar/mydir2",
            "foo/bar/mydir/deep",
            "foo/bar/mydir/deep/deeper",
            "foo/bar/mydir/deep/also",
            "foo/shallow"]

        ret = GetDeepestPaths(dirnames)

        d = [
            "bar/mydir",
            "bar/mydir2",
            "foo/bar/mydir/deep/deeper",
            "foo/bar/mydir/deep/also",
            "foo/shallow"]

        self.assertEqual(sorted(ret), sorted(d))


class Test_checksum(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -f foo.txt bar.txt')
        output = run('shelephant_checksum -f -q shelephant_dump.yaml')
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

    def test_hybrid(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -f foo.txt')
        output = run('shelephant_checksum -f -q')
        output = run('shelephant_hostinfo --force -f -c')

        output = run('shelephant_dump -f foo.txt bar.txt')
        output = run('shelephant_checksum -f -q -l shelephant_hostinfo.yaml')
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
        os.remove('shelephant_hostinfo.yaml')

    def test_recursive(self):

        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

        for letter in letters:
            with open('{0:s}.txt'.format(letter), 'w') as file:
                file.write(letter)

        files = ['{0:s}.txt'.format(letter) for letter in letters]

        keys = [
            'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb', # a
            '3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d', # b
            '2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6', # c
            '18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4', # d
            '3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca046dea', # e
            '252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111', # f
            'cd0aa9856147b6c5b4ff2b7dfee5da20aa38253099ef1b4a64aced233c9afe29', # g
        ]

        output = run('shelephant_dump -f -s {0:s}'.format(' '.join(files)))
        output = run('shelephant_checksum -f -q')

        data = YamlGetItem('shelephant_checksum.yaml')

        self.assertEqual(data, keys)

        ifiles = np.arange(len(files))
        np.random.shuffle(ifiles)

        output = run('shelephant_dump -f {0:s}'.format(' '.join([files[i] for i in ifiles[:3]])))
        output = run('shelephant_checksum -f -q')
        output = run('shelephant_hostinfo --force -f -c')

        np.random.shuffle(ifiles)

        output = run('shelephant_dump -f {0:s}'.format(' '.join([files[i] for i in ifiles])))
        output = run('shelephant_checksum -f -q -l shelephant_hostinfo.yaml')
        output = run('shelephant_hostinfo --force -f -c')

        output = run('shelephant_dump -f -s {0:s}'.format(' '.join(files)))
        output = run('shelephant_checksum -f -q -l shelephant_hostinfo.yaml')

        data = YamlGetItem('shelephant_checksum.yaml')

        self.assertEqual(data, keys)

        for file in files:
            os.remove(file)

        os.remove('shelephant_dump.yaml')
        os.remove('shelephant_checksum.yaml')
        os.remove('shelephant_hostinfo.yaml')


class Test_dump(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        for dirname in ['mydir']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mydir')

        with open('mydir/foo.txt', 'w') as file:
            file.write('foo')

        with open('mydir/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -f -s -o dump_1.yaml foo.txt bar.txt')
        output = run('shelephant_dump -f -s -o dump_2.yaml *.txt')
        output = run('shelephant_dump -f -s -o mydir/dump_3.yaml mydir/*.txt')

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

    def test_append(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        with open('foo.pdf', 'w') as file:
            file.write('foo')

        with open('bar.pdf', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -f foo.txt bar.txt')
        output = run('shelephant_dump -a foo.pdf bar.pdf')

        self.assertEqual(YamlRead('shelephant_dump.yaml'), ['foo.txt', 'bar.txt', 'foo.pdf', 'bar.pdf'])

        os.remove('foo.txt')
        os.remove('bar.txt')
        os.remove('foo.pdf')
        os.remove('bar.pdf')
        os.remove('shelephant_dump.yaml')


class Test_extract(unittest.TestCase):

    def test_single_path(self):

        data = {
            'foo' : ['foo.txt', 'bar.txt'],
            'bar' : ['foo.pdf', 'bar.pdf'],
            'key' : ['foo.key', 'bar.key'],
        }

        YamlDump('dump.yaml', data, force=True)

        output = run('shelephant_extract -f dump.yaml "foo"')

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

        output = run('shelephant_extract -f dump.yaml "/sub/foo" "foo"')

        self.assertEqual(YamlRead('dump.yaml'), {'foo': ['foo.txt', 'bar.txt'], 'sub': {'foo': ['foo.txt', 'bar.txt']}})

        os.remove('dump.yaml')

    def test_multiple_paths_squash(self):

        data = {
            'foo' : ['foo.txt', 'bar.txt'],
            'bar' : ['foo.pdf', 'bar.pdf'],
            'key' : ['foo.key', 'bar.key'],
            'sub' : {
                'foo' : ['foo2.txt', 'bar2.txt'],
                'bar' : ['foo2.pdf', 'bar2.pdf'],
                'key' : ['foo2.key', 'bar2.key'],
            },
        }

        YamlDump('dump.yaml', data, force=True)

        output = run('shelephant_extract -f dump.yaml --squash "/sub/foo" "foo"')

        self.assertEqual(YamlRead('dump.yaml'), ['foo2.txt', 'bar2.txt', 'foo.txt', 'bar.txt'])

        os.remove('dump.yaml')


class Test_merge(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -o main.yaml foo.txt')
        output = run('shelephant_dump -o branch.yaml bar.txt')
        output = run('shelephant_merge -f branch.yaml main.yaml')

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
        output = run('shelephant_merge -f dira/dump.yaml dirb/dump.yaml')

        self.assertEqual(YamlRead('dirb/dump.yaml'), ['foo.txt', 'bar.txt', '../dira/foo.txt', '../dira/bar.txt'])

        shutil.rmtree('dira')
        shutil.rmtree('dirb')


class Test_hostinfo(unittest.TestCase):

    def test_basic(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -f -s -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml')
        output = run('shelephant_get -f -q mydest/hostinfo.yaml')
        output = run('shelephant_dump -f -s -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')


    def test_remove(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        keys = [
            '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae',
            'fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9',
        ]

        output = run('shelephant_dump -f foo.txt bar.txt')
        output = run('shelephant_checksum -f -q')
        output = run('shelephant_hostinfo --force -f -c')
        output = run('shelephant_hostinfo --force --remove bar.txt')
        data = YamlRead('shelephant_hostinfo.yaml')

        self.assertEqual(data['files'], ['foo.txt'])
        self.assertEqual(data['checksum'], [keys[0]])

        os.remove('foo.txt')
        os.remove('bar.txt')
        os.remove('shelephant_dump.yaml')
        os.remove('shelephant_checksum.yaml')
        os.remove('shelephant_hostinfo.yaml')


class Test_get(unittest.TestCase):

    def test_basic(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        operations = [
            'bar.txt -> bar.txt',
            'foo.txt -> foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml')
        output = run('shelephant_get -f -d -q --colors none mydest/hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')

    def test_partial(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        shutil.copy('mysrc/foo.txt', 'mydest/foo.txt')

        operations = [
            'bar.txt -> bar.txt',
            'foo.txt == foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml')
        output = run('shelephant_get -f -d -q --colors none mydest/hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')

    def test_partial_localchecksum(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        with open('mysrc/car.txt', 'w') as file:
            file.write('car')

        with open('mysrc/dog.txt', 'w') as file:
            file.write('dog')

        shutil.copy('mysrc/foo.txt', 'mydest/foo.txt')
        shutil.copy('mysrc/dog.txt', 'mydest/dog.txt')

        operations = [
            'bar.txt -> bar.txt',
            'car.txt -> car.txt',
            'dog.txt == dog.txt',
            'foo.txt == foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')
        output = run('shelephant_hostinfo -o mydest/hostinfo.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml')
        output = run('shelephant_hostinfo -o mydest/local.yaml -f mydest/files.yaml -c mydest/checksum.yaml')
        output = run('shelephant_get -f -d -q --colors none -l mydest/local.yaml mydest/hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        output = run('shelephant_dump -f -s -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')


class Test_send(unittest.TestCase):

    def test_basic(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        with open('mydest/foobar.txt', 'w') as file:
            file.write('foobar')

        operations = [
            'bar.txt -> bar.txt',
            'foo.txt -> foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')
        output = run('shelephant_hostinfo --force -o hostinfo.yaml -f mydest/files.yaml -c mydest/checksum.yaml')
        output = run('shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        os.remove('mydest/foobar.txt')

        output = run('shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')
        os.remove('hostinfo.yaml')

    def test_empty_remote(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        operations = [
            'bar.txt -> bar.txt',
            'foo.txt -> foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_hostinfo --force -o hostinfo.yaml -p mydest')
        output = run('shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        output = run('shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml')
        output = run('shelephant_checksum -f -q -o mysrc/checksum.yaml mysrc/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')
        os.remove('hostinfo.yaml')


    def test_partial(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        shutil.copy('mysrc/foo.txt', 'mydest/foo.txt')

        operations = [
            'bar.txt -> bar.txt',
            'foo.txt == foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')
        output = run('shelephant_hostinfo --force -o hostinfo.yaml -f mydest/files.yaml -c mydest/checksum.yaml')
        output = run('shelephant_send -f -d -q --colors none mysrc/files.yaml hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        output = run('shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')
        os.remove('hostinfo.yaml')

    def test_partial_localchecksum(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        with open('mysrc/car.txt', 'w') as file:
            file.write('car')

        with open('mysrc/dog.txt', 'w') as file:
            file.write('dog')

        shutil.copy('mysrc/foo.txt', 'mydest/foo.txt')
        shutil.copy('mysrc/dog.txt', 'mydest/dog.txt')

        operations = [
            'bar.txt -> bar.txt',
            'car.txt -> car.txt',
            'dog.txt == dog.txt',
            'foo.txt == foo.txt',
        ]

        output = run('shelephant_dump --sort -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')
        output = run('shelephant_hostinfo --force -o hostinfo.yaml -f mydest/files.yaml -c mydest/checksum.yaml')
        output = run('shelephant_hostinfo --force -o local.yaml -f mysrc/files.yaml -c mysrc/checksum.yaml')
        output = run('shelephant_send -f -d -q --colors none -l local.yaml mysrc/files.yaml hostinfo.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), operations)

        output = run('shelephant_dump -f --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -f -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')
        os.remove('hostinfo.yaml')
        os.remove('local.yaml')


class Test_mv(unittest.TestCase):

    def test_basic(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_mv -f -q mysrc/files.yaml mydest')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')


class Test_cp(unittest.TestCase):

    def test_basic(self):

        for dirname in ['mysrc', 'mydest']:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)

        os.mkdir('mysrc')
        os.mkdir('mydest')

        with open('mysrc/foo.txt', 'w') as file:
            file.write('foo')

        with open('mysrc/bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -o mysrc/files.yaml mysrc/*.txt')
        output = run('shelephant_checksum -q -o mysrc/checksum.yaml mysrc/files.yaml')
        output = run('shelephant_cp -f -q mysrc/files.yaml mydest')
        output = run('shelephant_dump --sort -o mydest/files.yaml mydest/*.txt')
        output = run('shelephant_checksum -q -o mydest/checksum.yaml mydest/files.yaml')

        self.assertEqual(YamlRead('mysrc/files.yaml'), YamlRead('mydest/files.yaml'))
        self.assertEqual(YamlRead('mysrc/checksum.yaml'), YamlRead('mydest/checksum.yaml'))
        self.assertTrue(os.path.isfile('mysrc/foo.txt'))
        self.assertTrue(os.path.isfile('mysrc/bar.txt'))

        shutil.rmtree('mysrc')
        shutil.rmtree('mydest')


class Test_rm(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump foo.txt bar.txt')
        output = run('shelephant_rm -f shelephant_dump.yaml')

        self.assertFalse(os.path.isfile('foo.txt'))
        self.assertFalse(os.path.isfile('bar.txt'))

        os.remove('shelephant_dump.yaml')


class Test_parse(unittest.TestCase):

    def test_basic(self):

        with open('foo.txt', 'w') as file:
            file.write('foo')

        with open('bar.txt', 'w') as file:
            file.write('bar')

        output = run('shelephant_dump -f foo.txt bar.txt')
        output = run('shelephant_parse shelephant_dump.yaml')

        self.assertEqual(list(filter(None, output.split('\n'))), ['- foo.txt', '- bar.txt'])

        os.remove('shelephant_dump.yaml')
        os.remove('foo.txt')
        os.remove('bar.txt')


if __name__ == '__main__':

    unittest.main()
