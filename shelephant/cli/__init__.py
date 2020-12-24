import docopt
import click
import os
import sys
import yaml
import operator
import functools
import subprocess
import collections.abc
import shutil
import math


def FlattenList_detail(data):
    r'''
See https://stackoverflow.com/a/17485785/2646505
    '''

    for item in data:
        if isinstance(item, collections.abc.Iterable) and not isinstance(item, str):
            for x in FlattenList(item):
                yield x
        else:
            yield item


def FlattenList(data):
    r'''
Flatten a nested list to a one dimensional list.
    '''
    return list(FlattenList_detail(data))


def Squash_detail(data, parent_key='', sep='_'):
    r'''
See https://stackoverflow.com/a/6027615/2646505
    '''

    items = []

    for k, v in data.items():

        new_key = parent_key + sep + k if parent_key else k

        if isinstance(v, collections.abc.MutableMapping):
            items.extend(Squash_detail(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def Squash(data):
    r'''
Squash a dictionary to a single list.
    '''

    return FlattenList(list(Squash_detail(data).values()))


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


def YamlPrint(data):
    r'''
Print data formatted as YAML.
    '''
    print(yaml.dump(data, default_flow_style=False, default_style=''))


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


def GetSHA256(filename, size = 2 ** 10):
    r'''
Get SHA256 for a file.
    '''

    import hashlib

    h = hashlib.sha256()

    with open(filename, 'rb') as f:
        for byte_block in iter(lambda: f.read(size * h.block_size), b""):
            h.update(byte_block)
        return h.hexdigest()


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


def ShelephantCopy(operation, source, key, dest_dir, theme_name, checksum, quiet, force):
    r'''
Copy/move files.

:arguments:

    **operation** (``'copy'`` | ``'move'``)
        Select type of operation.

    **source** (``<str>``)
        YAML-file with filenames.
        The filenames are assumed either absolute, or relative to the input YAML-file.

    **key** (``<str>``)
        Path in the YAML-file, separated by "/".
        Use "/" for root.

    **dest_dir** (``<str>``)
        The destination.

    **theme_name** (``<str>``)
        The name of the color-theme. See ``Theme``.

    **checksum** (``True`` | ``False`` | ``<list<str>>``)
        Use checksum to skip files that are the same.

    **quiet** (``True`` | ``False``)
        Proceed without printing progress.

    **force** (``True`` | ``False``)
        Continue without prompt.
    '''

    files = YamlGetItem(source, key)
    src_dir = os.path.dirname(source)

    if not os.path.isdir(dest_dir):
        if not force:
            print('mkdir -p {0:s}'.format(dest_dir))
            if not click.confirm('Proceed?'):
                return 1
        os.makedirs(dest_dir)

    src = PrefixPaths(src_dir, files)
    dest = PrefixPaths(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    theme = Theme(theme_name.lower())

    if checksum == True:
        checksum = [GetSHA256(file) for file in files]

    for i in range(n):
        if os.path.isfile(dest[i]):
            if checksum:
                if GetSHA256(dest[i]) == GetSHA256(src[i]):
                    skip[i] = True
                    continue
            overwrite[i] = True
            continue
        create[i] = True

    print('-----')
    print('- from dir. : ' + os.path.normpath(src_dir))
    print('- to dir.   : ' + os.path.normpath(dest_dir))
    print('-----')

    l = max([len(file) for file in files])

    for i in range(n):
        if create[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['bright']).format(),
                String('->', color=theme['bright']).format(),
                String(files[i], color=theme['new']).format()
            ))
        elif skip[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['skip']).format(),
                String('==', color=theme['skip']).format(),
                String(files[i], color=theme['skip']).format()
            ))
        elif overwrite[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['bright']).format(),
                String('=>', color=theme['bright']).format(),
                String(files[i], color=theme['overwrite']).format()
            ))

    if all(skip):
        return 0

    if not force:
        if not click.confirm('Proceed?'):
            return 1

    ncp = n - sum(skip)
    l = int(math.log10(ncp) + 1)
    fmt = '({0:' + str(l) + 'd}/' + ('{0:' + str(l) + 'd}').format(ncp) + ') {1:s}'

    if operation == 'move':

        for i in range(n):
            if not skip[i]:
                if not quiet:
                    print(fmt.format(i, dest[i]))
                os.rename(src[i], dest[i])

    elif operation == 'copy':

        for i in range(n):
            if not skip[i]:
                if not quiet:
                    print(fmt.format(i, dest[i]))
                shutil.copy(src[i], dest[i])


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
