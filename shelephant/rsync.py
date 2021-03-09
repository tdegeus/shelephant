
import click
import re
import os
import numpy as np

from .external import exec_cmd

def _rsync(
    source_dir,
    dest_dir,
    tempfilename,
    files,
    force=False,
    verbose=False,
    progress=True):
    r'''
Copy files to a destination using ``rsync -a --files-from``.

:param str source_dir: Source directory.
:param str dest_dir: Source directory.
:param str tempfilename: Path of a temporary file to use to direct ``rsync --files-from``.
:param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
:param bool force: Continue without prompt.
:param bool verbose: Verbose commands.
:param bool progress: Show progress bar.
    '''

    assert type(tempfilename) == str

    if not force:
        if os.path.isfile(tempfilename):
            if not click.confirm('Overwrite "{0:s}"?'.format(tempfilename)):
                raise IOError('Cancelled')

    open(tempfilename, 'w').write('\n'.join(files))

    # Run without printing output

    if not progress:

        cmd = 'rsync -a --files-from="{files:s}" "{source_dir:s}" "{dest_dir:s}"'.format(
            source_dir=source_dir, dest_dir=dest_dir, files=tempfilename)

        return exec_cmd(cmd, verbose)

    # Run while printing output

    cmd = 'rsync -aP --files-from="{files:s}" "{source_dir:s}" "{dest_dir:s}"'.format(
        source_dir=source_dir, dest_dir=dest_dir, files=tempfilename)

    if verbose:
        print(cmd)

    pbar = tqdm.tqdm(total=len(files))
    sbar = tqdm.tqdm(unit='B', unit_scale=True)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    for line in iter(process.stdout.readline, b''):
        line = line.decode("utf-8")
        if re.match(r'(.*)(xf)([e]?)(r\#)([0-9])(.*)(to\-ch)([e]?[c]?)(k\=)([0-9])(.*)', line):
            e = int(list(filter(None, line.split(" ")))[-6].replace(",", ""))
            pbar.update()
            sbar.update(e)


def from_remote(
    hostname,
    source_dir,
    dest_dir,
    tempfilename,
    files,
    force=False,
    verbose=False,
    progress=True):
    r'''
Copy files to a remote system using ``rsync -a --files-from``.

:param str hostname: Hostname.
:param str source_dir: Source directory.
:param str dest_dir: Source directory.
:param str tempfilename: Path of a temporary file to use to direct ``rsync --files-from``.
:param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
:param bool force: Continue without prompt.
:param bool verbose: Verbose commands.
:param bool progress: Show progress bar.
    '''

    return _rsync(
        source_dir = hostname + ":" + source_dir,
        dest_dir = dest_dir,
        tempfilename = tempfilename,
        files = files,
        force = force,
        verbose = verbose,
        progress = progress)


def to_remote(
    hostname,
    source_dir,
    dest_dir,
    tempfilename,
    files,
    force=False,
    verbose=False,
    progress=True):
    r'''
Copy files from a remote system using ``rsync -a --files-from``.

:param str hostname: Hostname.
:param str source_dir: Source directory.
:param str dest_dir: Source directory.
:param str tempfilename: Path of a temporary file to use to direct ``rsync --files-from``.
:param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
:param bool force: Continue without prompt.
:param bool verbose: Verbose commands.
:param bool progress: Show progress bar.
    '''

    return _rsync(
        source_dir = source_dir,
        dest_dir = hostname + ":" + dest_dir,
        tempfilename = tempfilename,
        files = files,
        force = force,
        verbose = verbose,
        progress = progress)


def diff(
    source_dir,
    dest_dir,
    tempfilename,
    files,
    checksum=False,
    force=False,
    verbose=False):
    r'''
Check if files are different using *rsync*.
*rsync* uses basic criteria such as file size and creation and modification date.
This is much faster than using checksums but is only approximate.
See `rsync manual <https://www.samba.org/ftp/rsync/rsync.html>`_.

:param str source_dir: Source directory.
:param str dest_dir: Source directory.
:param str tempfilename: Path of a temporary file to use to direct ``rsync --files-from``.
:param list files: List of file-paths (relative to ``source_dir`` and ``dest_dir``).
:param bool checksum: Use checksum to test file difference.
:param bool force: Continue without prompt.
:param bool verbose: Verbose commands.
    '''

    files = [os.path.normpath(file) for file in files]

    assert type(tempfilename) == str

    if not force:
        if os.path.isfile(tempfilename):
            if not click.confirm('Overwrite "{0:s}"?'.format(tempfilename)):
                raise IOError('Cancelled')

    open(tempfilename, 'w').write('\n'.join(files))

    # Run without printing output

    opt = '-nai'

    if checksum:
        opt += 'c'

    cmd = 'rsync {opt:s} --files-from="{files:s}" "{source_dir:s}" "{dest_dir:s}"'.format(
        source_dir=source_dir, dest_dir=dest_dir, files=tempfilename, opt=opt)

    lines = list(filter(None, exec_cmd(cmd, verbose).split('\n')))
    lines = [line for line in lines if line[1] == 'f']

    if len(lines) == 0:
        return {
            'skip' : np.ones((len(files)), dtype=np.bool),
            'create' : np.zeros((len(files)), dtype=np.bool),
            'overwrite' : np.zeros((len(files)), dtype=np.bool),
        }

    check_paths = [line.split(' ')[1] for line in lines]
    mode = np.zeros((len(check_paths)), dtype=np.int16)

    for i, line in enumerate(lines):
        if line[0] == '>':
            if line[2] == '+':
                mode[i] = 1 # create
            else:
                mode[i] = 2 # overwrite
        elif line[0] == '.':
            pass
        else:
            raise IOError('Unknown cryptic output "{0:s}"'.format(line))

    sorter = np.argsort(files)
    source_paths = np.array(files, dtype=str)[sorter]

    i = np.argsort(check_paths)
    check_paths = np.array(check_paths, dtype=str)[i]
    mode = mode[i]

    test = np.in1d(source_paths, check_paths)

    idx = np.searchsorted(check_paths, source_paths)
    idx = np.where(test, idx, 0)
    ret = np.where(test, mode[idx], 0)
    ret = ret.astype(np.int16)
    out = np.empty_like(ret)
    out[sorter] = ret

    return {
        'skip' : out == 0,
        'create' : out == 1,
        'overwrite' : out == 2,
    }
