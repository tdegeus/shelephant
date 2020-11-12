import docopt
import click
import os
import sys
import yaml
import operator
import functools
import subprocess


def ExecCommand(cmd, verbose=False):
    r'''
Run command, optionally verbose command and output, and return output.
    '''

    if verbose:
        print(cmd)

    out = subprocess.check_output(cmd, shell=True).decode('utf-8')

    if verbose:
        print(out)

    return out


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

def GetString(filename, path=[]):
    r'''
Get a single path.
    '''
    files = GetList(filename, path)
    assert len(files) == 1
    return filename[0]


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


def PrefixPaths(prefix, files):
    r'''
Add prefix to list of filenames.
Skip if all paths are absolute paths.
    '''

    isabs = [os.path.isabs(file) for file in files]

    if any(isabs) and not all(isabs):
        Error('Specify either relative or absolute files-paths')

    if all(isabs):
        return files

    return [os.path.normpath(os.path.join(prefix, file)) for file in files]


def Theme(theme=None):
    r'''
Return dictionary of colors.

.. code-block:: python

    {
        'selection' : '...',
        'free' : '...',
        'error' : '...',
        'warning' : '...',
        'low' : '...',
    }

:options:

    **theme** ([``'dark'``] | ``<str>``)
        Select color-theme.
    '''

    if theme == 'dark':
        return \
        {
            'new' : '1;32',
            'overwrite': '1;31',
            'skip' : '1;30',
        }

    return \
    {
        'new' : '',
        'overwrite': '',
        'skip' : '',
    }


class String:
    r'''
Rich string.

.. note::

    All options are attributes, that can be modified at all times.

:options:

    **data** (``<str>`` | ``None``)
        The data.

    **width** ([``None``] | ``<int>``)
        Print width (formatted print only).

    **color** ([``None``] | ``<str>``)
        Print color, e.g. "1;32" for bold green (formatted print only).

    **align** ([``'<'``] | ``'>'``)
        Print alignment (formatted print only).

    **dummy** ([``0``] | ``<int>`` | ``<float>``)
        Dummy numerical value.

:methods:

    **A.format()**
        Formatted string.

    **str(A)**
        Unformatted string.

    **A.isnumeric()**
        Return if the "data" is numeric.

    **int(A)**
        Dummy integer.

    **float(A)**
        Dummy float.
    '''

    def __init__(self, data, width=None, align='<', color=None, dummy=0):

        self.data  = data
        self.width = width
        self.color = color
        self.align = align
        self.dummy = dummy

    def format(self):
        r'''
Return formatted string: align/width/color are applied.
        '''

        if self.width and self.color:
            fmt = '\x1b[{color:s}m{{0:{align:s}{width:d}.{width:d}s}}\x1b[0m'.format(**self.__dict__)
        elif self.width:
            fmt = '{{0:{align:s}{width:d}.{width:d}s}}'.format(**self.__dict__)
        elif self.color:
            fmt = '\x1b[{color:s}m{{0:{align:s}s}}\x1b[0m'.format(**self.__dict__)
        else:
            fmt = '{{0:{align:s}s}}'.format(**self.__dict__)

        return fmt.format(str(self))

    def isnumeric(self):
        r'''
Return if the "data" is numeric : always zero for this class.
        '''
        return False

    def __str__(self):
        return str(self.data)

    def __int__(self):
        return int(self.dummy)

    def __float__(self):
        return float(self.dummy)

    def __repr__(self):
        return str(self)

    def __lt__(self,other):
        return str(self) < str(other)
