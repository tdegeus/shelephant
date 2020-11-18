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
Run command, optionally verbose command and its output, and return output.
    '''

    if verbose:
        print(cmd)

    ret = subprocess.check_output(cmd, shell=True).decode('utf-8')

    if verbose:
        print(ret)

    return ret


def Error(text):
    r'''
Command-line error: show message and quit the program with exit code "1"
    '''

    print(text)
    sys.exit(1)


def YamlRead(filename):
    r'''
Read YAML file and return its content as ``list`` or ``dict``.
    '''

    if not os.path.isfile(filename):
        Error('"{0:s} does not exist'.format(filename))

    with open(filename, 'r') as file:
        return yaml.load(file.read(), Loader=yaml.FullLoader)


def YamlDump(filename, data, force=False):
    r'''
Dump data (as ``list`` or ``dict``) to YAML file.
Unless ``force = True`` the function prompts before overwriting an existing file.
    '''

    if not force:
        if os.path.isfile(filename):
            if not click.confirm('Overwrite "{0:s}"?'.format(filename)):
                sys.exit(1)

    with open(filename, 'w') as file:
        ret = yaml.dump(data, file)


def YamlGetItem(filename, key=[]):
    r'''
Get an item from a YAML file.
Optionally the key to the item can be specified as a list. E.g.
*   ``[]`` for a YAML file containing only a list.
*   ``['foo']`` for a plain YAML file.
*   ``['key', 'to', foo']`` for a YAML file with nested items.
    '''

    data = YamlRead(filename)

    if len(key) == 0 and type(data) != list:
        Error('Specify key for "{1:s}"'.format(filename))

    if len(key) > 0:
        try:
            return functools.reduce(operator.getitem, key, data)
        except:
            Error('"{0:s}" not in "{1:s}"'.format(key, filename))

    return data


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
Add prefix to a list of filenames.
Skip if all paths are absolute paths.
    '''

    isabs = [os.path.isabs(file) for file in files]

    if any(isabs) and not all(isabs):
        Error('Specify either relative or absolute files-paths')

    if all(isabs):
        return files

    return [os.path.normpath(os.path.join(prefix, file)) for file in files]


def ChangeRootOfRelativePaths(files, old_root, new_root, in_place=False):
    r'''
Change the root of relative paths.
Skip if all paths are absolute paths.

If ``in_place = True`` the input list is modified 'in place' (and a pointer to it is returned),
otherwise a new list is returned.
    '''

    isabs = [os.path.isabs(file) for file in files]

    if any(isabs) and not all(isabs):
        Error('Specify either relative or absolute files-paths')

    if all(isabs):
        return files

    if not in_place:
        return [os.path.relpath(os.path.abspath(os.path.join(old_root, file)), new_root) for file in files]

    for i in range(len(files)):
        files[i] = os.path.relpath(os.path.abspath(os.path.join(old_root, files[i])), new_root)

    return files


def IsOnRemote(host, source, verbose=False):
    r'''
Check if a file exists on a remote system. Uses ``ssh``.
    '''

    cmd = 'ssh {host:s} test -f "{source:s}" && echo found || echo not found'.format(
        host=host, source=source)

    ret = ExecCommand(cmd, args['--verbose'])

    if ret == 'found':
        return True

    return False


def CopyFromRemote(host, source, dest, verbose=False):
    r'''
Copy a file from a remote system. Uses ``scp``.
    '''

    cmd = 'scp {host:s}:{source:s} {dest:s}'.format(
        host=host, source=source, dest=dest)

    ExecCommand(cmd, verbose)


def CopyToRemote(host, source, dest, verbose=False):
    r'''
Copy a file to a remote system. Uses ``scp``.
    '''

    cmd = 'scp {source:s} {host:s}:{dest:s}'.format(
        host=host, source=source, dest=dest)

    ExecCommand(cmd, verbose)


def Theme(theme=None):
    r'''
Return dictionary of colors.

.. code-block:: python

    {
        'new' : '...',
        'overwrite' : '...',
        'skip' : '...',
        'bright' : '...',
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
            'bright' : '1;37',
        }

    return \
    {
        'new' : '',
        'overwrite': '',
        'skip' : '',
        'bright' : '',
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
