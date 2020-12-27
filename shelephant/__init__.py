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
import numpy as np


__version__ = '0.9.0'


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


def MakeDir(dirname, force=False):
    r'''
Create a directory if it does not yet exist.
    '''

    if len(dirname) == 0:
        return 0

    if os.path.isdir(dirname):
        return 0

    if not force:
        print('mkdir -p {0:s}'.format(dirname))
        if not click.confirm('Proceed?'):
            return 1

    os.makedirs(dirname)


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


def GetChecksums(filepaths, yaml_hostinfo=None, hybrid=False):
    r'''
Compute the checksums for ``filepaths``.

:arguments:

    **filepaths** (``<list<str>>``)
        List of file-paths.

:option:

    **yaml_hostinfo** (``<str>```)
        File-path of a host-info file (see ``shelephant_hostinfo``).
        If specified the checksums are **not** computed, but exclusively read from the
        host-file. The user is responsible for keeping them up-to-date.

    **hybrid** ([``False``] | ``True``)
        If ``True``, the function first tries to read from ``yaml_hostinfo``, and then
        computes missing items on the fly.

:returns:

    (``<list<str>>``)
        List of checksums, of same length as ``filepaths``.
        The entry is ``None`` if no checksum was found/read.
    '''

    n = len(filepaths)
    ret = [None for i in range(n)]

    # Compute

    if not yaml_hostinfo:

        for i in range(n):
            if os.path.isfile(filepaths[i]):
                ret[i] = GetSHA256(filepaths[i])

        return ret

    # Read pre-computed

    data = YamlRead(yaml_hostinfo)
    files = data['files']
    prefix = data['prefix']
    checksum = data['checksum']
    paths = PrefixPaths(prefix, files)

    for i in range(n):
        if filepaths[i] in paths:
            j = np.argwhere([path == filepaths[i] for path in paths]).ravel()[0]
            ret[i] = checksum[j]

    if hybrid:
        for i in range(n):
            if ret[i] is None:
                if os.path.isfile(filepaths[i]):
                    ret[i] = GetSHA256(filepaths[i])

    return ret


def ShelephantCopy(
    copy_function,
    files,
    src_dir,
    dest_dir,
    checksum = False,
    quiet = False,
    force = False,
    theme_name = 'none',
    yaml_hostinfo_src = None,
    yaml_hostinfo_dest = None):
    r'''
Copy/move files.

:arguments:

    **copy_function** (``<function>``)
        Function to perform the copy. E.g. `os.rename` or `shutil.copy`.

    **files** (``<list<<str>>``)
        Filenames (will be prepended by ``src_dir`` and ``dest_dir``).

    **src_dir** (``<str>``)
        The destination directory.

    **dest_dir** (``<str>``)
        The destination directory.

:options:

    **checksum** ([``False``] | ``True``)
        Use checksum to skip files that are the same.

    **quiet** ([``False``] | ``True``)
        Proceed without printing progress.

    **force** ([``False``] | ``True``)
        Continue without prompt.

    **theme_name** ([``'none'``] | ``<str>``)
        The name of the color-theme. See ``Theme``.

    **yaml_hostinfo_src, yaml_hostinfo_src** (``<str>``)
        Filename of host-files for the source and destination.
        These files contain existing files and optionally checksums, see ``shelephant_hostinfo``.
        Specify these files *only* to use precomputed checksums.
    '''

    src = PrefixPaths(src_dir, files)
    dest = PrefixPaths(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    theme = Theme(theme_name.lower())

    for file in src:
        if not os.path.isfile(file):
            Error('"{0:s}" does not exists'.format(file))

    if MakeDir(dest_dir, force):
        return 1

    if checksum == True:
        src_checksums = GetChecksums(src, yaml_hostinfo_src)
        dest_checksums = GetChecksums(dest, yaml_hostinfo_dest)

    for i in range(n):
        if os.path.isfile(dest[i]):
            if checksum:
                if (src_checksums[i] == dest_checksums[i]) and (src_checksums[i] is not None):
                    skip[i] = True
                    continue
            overwrite[i] = True
            continue
        create[i] = True

    l = max([len(file) for file in files])
    ncreate = sum(create)
    noverwrite = sum(overwrite)
    nskip = sum(skip)
    pskip = nskip <= 100
    skip_meesage = ' (not printed)' if not pskip else ''

    summary = []
    summary += ['- from dir. : ' + os.path.normpath(src_dir)]
    summary += ['- to dir.   : ' + os.path.normpath(dest_dir)]
    summary += ['- ' + ', '.join([
        String('create (->): {0:d}'.format(ncreate), color=theme['new']).format(),
        String('overwrite (=>): {0:d}'.format(noverwrite), color=theme['overwrite']).format(),
        String('skip (==): {0:d}{1:s}'.format(nskip, skip_meesage), color=theme['skip']).format()])]

    if ncreate + noverwrite <= 100:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    for i in range(n):
        if create[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['bright']).format(),
                String('->', color=theme['bright']).format(),
                String(files[i], color=theme['new']).format()
            ))
        elif skip[i] and pskip:
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

    if ncreate + noverwrite > 100:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    if all(skip):
        return 0

    if not force:
        if not click.confirm('Proceed?'):
            return 1

    ncp = n - nskip
    l = int(math.log10(ncp) + 1)
    fmt = '({0:' + str(l) + 'd}/' + ('{0:' + str(l) + 'd}').format(ncp) + ') {1:s}'
    j = 0

    for i in range(n):
        if not skip[i]:
            if not quiet:
                j += 1
                print(fmt.format(j, files[i]))
            copy_function(src[i], dest[i])


def ShelephantCopySSH(
    copy_function,
    host,
    files,
    src_dir,
    dest_dir,
    checksum = False,
    quiet = False,
    force = False,
    verbose = False,
    theme_name = 'none',
    yaml_hostinfo_src = None,
    yaml_hostinfo_dest = None):
    r'''
Send/get files.

:arguments:

    **copy_function** (``<function>``)
        Function to perform the copy. E.g. `CopyFromRemote` or `CopyFromRemote`.

    **host** (``<str>``)
        Host-name.

    **files** (``<list<<str>>``)
        Filenames (will be prepended by ``src_dir`` and ``dest_dir``).

    **src_dir** (``<str>``)
        The destination directory.

    **dest_dir** (``<str>``)
        The destination directory.

:options:

    **checksum** ([``False``] | ``True``)
        Use checksum to skip files that are the same.

    **quiet** ([``False``] | ``True``)
        Proceed without printing progress.

    **force** ([``False``] | ``True``)
        Continue without prompt.

    **verbose** ([``False``] | ``True``)
        Verbose all operations.

    **theme_name** ([``'none'``] | ``<str>``)
        The name of the color-theme. See ``Theme``.

    **yaml_hostinfo_src, yaml_hostinfo_src** (``<str>``)
        Filename of host-files for the source and destination.
        These files contain existing files and optionally checksums, see ``shelephant_hostinfo``.
        Specify these files *only* to use precomputed checksums.
    '''

    src = PrefixPaths(src_dir, files)
    dest = PrefixPaths(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    dest_exists = [False for i in range(n)]
    theme = Theme(theme_name)

    if checksum == True:
        src_checksums = GetChecksums(src, yaml_hostinfo_src)
        dest_checksums = GetChecksums(dest, yaml_hostinfo_dest)

    if copy_function == CopyToRemote:
        if yaml_hostinfo_dest:
            f = YamlRead(yaml_hostinfo_dest)['files']
            for i in range(n):
                if files[i] in f:
                    dest_exists[i] = True
    else:
        for i in range(n):
            if os.path.isfile(dest[i]):
                dest_exists[i] = True

    for i in range(n):
        if dest_exists[i]:
            if checksum:
                if (src_checksums[i] == dest_checksums[i]) and (src_checksums[i] is not None):
                    skip[i] = True
                    continue
            overwrite[i] = True
            continue
        create[i] = True

    l = max([len(file) for file in files])
    ncreate = sum(create)
    noverwrite = sum(overwrite)
    nskip = sum(skip)
    pskip = nskip <= 100
    skip_meesage = ' (not printed)' if not pskip else ''

    summary = []
    if copy_function == CopyToRemote:
        summary += ['- to host           : ' + host]
        summary += ['- from dir. (local) : ' + os.path.normpath(src_dir)]
        summary += ['- to dir. (remote)  : ' + os.path.normpath(dest_dir)]
    else:
        summary += ['- from host          : ' + host]
        summary += ['- from dir. (remote) : ' + os.path.normpath(src_dir)]
        summary += ['- to dir. (local)    : ' + os.path.normpath(dest_dir)]
    summary += ['- ' + ', '.join([
        String('create (->): {0:d}'.format(ncreate), color=theme['new']).format(),
        String('overwrite (=>): {0:d}'.format(noverwrite), color=theme['overwrite']).format(),
        String('skip (==): {0:d}{1:s}'.format(nskip, skip_meesage), color=theme['skip']).format()])]

    if ncreate + noverwrite <= 100:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    for i in range(n):
        if create[i]:
            print('{0:s} {1:s} {2:s}'.format(
                String(files[i], width=l, color=theme['bright']).format(),
                String('->', color=theme['bright']).format(),
                String(files[i], color=theme['new']).format()
            ))
        elif skip[i] and pskip:
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

    if ncreate + noverwrite > 100:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    if all(skip):
        return 0

    if not force:
        if not click.confirm('Proceed?'):
            return 1

    ncp = n - sum(skip)
    l = int(math.log10(ncp) + 1)
    fmt = '({0:' + str(l) + 'd}/' + ('{0:' + str(l) + 'd}').format(ncp) + ') {1:s}'
    j = 0

    for i in range(n):
        if not skip[i]:
            if not quiet:
                j += 1
                print(fmt.format(j, files[i]))
            copy_function(host, src[i], dest[i], verbose)


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

