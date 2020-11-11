import docopt
import click
import os
import sys
import yaml
import operator
import functools


def Error(text):
    r'''
Command-line error: show message and quit with exit code "1"
    '''

    print(text)
    sys.exit(1)


def ReadYaml(filename):
    r'''
Read YAML file.
    '''

    if not os.path.isfile(filename):
        Error('"{0:s} does not exist'.format(filename))

    return yaml.load(open(filename, 'r').read(), Loader=yaml.FullLoader)


def GetList(filename, path=[]):
    r'''
Get list of paths.
    '''

    data = ReadYaml(filename)

    if len(path) == 0 and type(data) != list:
        Error('Specify path for "{1:s}"'.format(filename))

    if len(path) > 0:
        try:
            return functools.reduce(operator.getitem, path, data)
        except:
            Error('"{0:s}" not in "{1:s}"'.format(path, filename))

    return data


def YamlDump(filename, data, force=False):
    r'''
Dump data to YAML file.
    '''

    if not force:
        if os.path.isfile(filename):
            if not click.confirm('Overwrite "{0:s}"?'.format(filename)):
                sys.exit(1)

    with open(filename, 'w') as file:
        ret = yaml.dump(data, file)


def GetSHA256(filename):
    r'''
Get SHA256 for a file.
    '''

    import hashlib

    sha256_hash = hashlib.sha256()

    with open(filename, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
