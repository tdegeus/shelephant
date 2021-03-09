r'''
Implementation details.
Not part of public API.

(c) Tom de Geus, 2021, MIT
'''


import click
import numpy as np
import os
import tqdm

from .checksum import get
from .path import makedirs
from .relpath import add_prefix
from .rich import String
from .rich import theme
from .rsync import diff
from .yaml import read


def copy(
    copy_function,
    files,
    src_dir,
    dest_dir,
    checksum = False,
    check_rsync = None,
    quiet = False,
    force = False,
    print_details = True,
    print_summary = True,
    print_all = False,
    theme_name = 'none',
    yaml_hostinfo_src = None,
    yaml_hostinfo_dest = None):
    r'''
Copy/move files.

:param function copy_function:
    Function to perform the copy.
    Called with ``copy_function(source_path, dest_path)``.
    E.g. ``os.rename``.

:type files: list of str
:param files: Filenames (will be prepended by ``src_dir`` and ``dest_dir``).

:param str src_dir: The source directory.
:param str dest_dir: The destination directory.
:param bool checksum: Use checksum to skip files that are the same.
:param str check_rsync: Use rsync to check files to skip, specify temporary file name.
:param bool quiet: Proceed without printing progress.
:param bool force: Continue without prompt.
:param bool print_details: Print copy details.
:param bool print_summary: Print copy summary.
:param bool print_all: If ``False`` auto-truncation of long output is applied.

:type theme_name: str or None
:param theme_name: The name of the color-theme. See :py:mod:`shelephant.theme`.

:type yaml_hostinfo_src: str, optional
:param yaml_hostinfo_src:
    Filename of hostinfo for the source, see :py:mod:`shelephant.cli.hostinfo`.
    Specify these files *only* to use precomputed checksums.

:type yaml_hostinfo_dest: str, optional
:param yaml_hostinfo_dest:
    Filename of hostinfo for the destination, see :py:mod:`shelephant.cli.hostinfo`.
    Specify these files *only* to use precomputed checksums.
    '''

    assert type(files) == list

    if len(files) == 0:
        if not quiet:
            print('Nothing to do')
        return

    src = add_prefix(src_dir, files)
    dest = add_prefix(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    color = theme(theme_name.lower())

    for file in src:
        if not os.path.isfile(file):
            raise IOError('Input file "{0:s}" does not exists'.format(file))

    if not os.path.isdir(dest_dir) and len(dest_dir) > 0:

        create = [True for i in range(n)]

    elif check_rsync is not None:

        tmp = diff(
            source_dir = src_dir,
            dest_dir = dest_dir,
            tempfilename = check_rsync,
            files = files,
            checksum = checksum,
            force = force)

        skip = tmp['skip']
        create = tmp['create']
        overwrite = tmp['overwrite']

    else:

        if checksum:
            src_checksums = get(src, yaml_hostinfo_src, progress=not quiet)
            dest_checksums = get(dest, yaml_hostinfo_dest, progress=not quiet)

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
    pcreate = not ((noverwrite > 0 and ncreate > 100) or ncreate > 300) or print_all
    pskip = (nskip <= 100) or print_all
    pcreate_message = ' (not printed)' if not pcreate else ''
    pskip_message = ' (not printed)' if not pskip else ''

    overview = []
    if ncreate > 0:
        overview += [String('create (->): {0:d}{1:s}'.format(ncreate, pcreate_message), color=color['new']).format()]
    if noverwrite > 0:
        overview += [String('overwrite (=>): {0:d}'.format(noverwrite), color=color['overwrite']).format()]
    if nskip > 0:
        overview += [String('skip (==): {0:d}{1:s}'.format(nskip, pskip_message), color=color['skip']).format()]

    summary = []
    summary += ['- source : ' + os.path.normpath(src_dir)]
    summary += ['- dest   : ' + os.path.normpath(dest_dir)]
    summary += ['- ' + ', '.join(overview)]

    if ncreate + noverwrite <= 100 and print_summary:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    if print_details:
        for i in range(n):
            if create[i] and pcreate:
                print('{0:s} {1:s} {2:s}'.format(
                    String(files[i], width=l, color=color['bright']).format(),
                    String('->', color=color['bright']).format(),
                    String(files[i], color=color['new']).format()
                ))
            elif skip[i] and pskip:
                print('{0:s} {1:s} {2:s}'.format(
                    String(files[i], width=l, color=color['skip']).format(),
                    String('==', color=color['skip']).format(),
                    String(files[i], color=color['skip']).format()
                ))
            elif overwrite[i]:
                print('{0:s} {1:s} {2:s}'.format(
                    String(files[i], width=l, color=color['bright']).format(),
                    String('=>', color=color['bright']).format(),
                    String(files[i], color=color['overwrite']).format()
                ))

    if ncreate + noverwrite > 100 and print_summary:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    if all(skip):
        return 0

    if not force:
        if not click.confirm('Proceed?'):
            raise IOError('Cancelled')

    makedirs(list(set([os.path.dirname(i) for i in dest])))

    i = np.argwhere(np.not_equal(skip, True)).ravel()
    src = np.array(src)[i]
    dest = np.array(dest)[i]
    files = np.array(files)[i]

    for i in tqdm.trange(len(files), disable=quiet):
        copy_function(src[i], dest[i])


def copy_ssh(
    copy_function,
    use_rsync,
    host,
    files,
    src_dir,
    dest_dir,
    to_remote,
    checksum = False,
    check_rsync = None,
    quiet = False,
    force = False,
    print_details = True,
    print_summary = True,
    print_all = False,
    verbose = False,
    theme_name = 'none',
    yaml_hostinfo_src = None,
    yaml_hostinfo_dest = None,
    tempfilename = None):
    r'''
Get/send files.

:param function copy_function:
    Function to perform the copy.
    Called differently depending on ``use_rsync``.

:param bool use_rsync: Signal if ``copy_function`` uses *rsync*.
:param str host: Host-name

:type files: list of str
:param files: Filenames (will be prepended by ``src_dir`` and ``dest_dir``).

:param str src_dir: The source directory.
:param str dest_dir: The destination directory.
:param bool to_remote: Sets direction of copy operation.
:param bool checksum: Use checksum to skip files that are the same.
:param str check_rsync: Use rsync to check files to skip, specify temporary file name.
:param bool quiet: Proceed without printing progress.
:param bool force: Continue without prompt.
:param bool print_details: Print copy details.
:param bool print_summary: Print copy summary.
:param bool print_all: If ``False`` auto-truncation of long output is applied.

:type theme_name: str or None
:param theme_name: The name of the color-theme. See :py:fun:`shelephant.rich.theme`.

:type yaml_hostinfo_src: str, optional
:param yaml_hostinfo_src:
    Filename of hostinfo for the source, see :py:mod:`shelephant.cli.hostinfo`.
    Specify these files *only* to use precomputed checksums.

:type yaml_hostinfo_dest: str, optional
:param yaml_hostinfo_dest:
    Filename of hostinfo for the destination, see :py:mod:`shelephant.cli.hostinfo`.
    Specify these files *only* to use precomputed checksums.

:param str tempfilename: Filename for temporary file to use (e.g. for ``rsync``).
    '''

    assert type(files) == list

    if len(files) == 0:
        if not quiet:
            print('Nothing to do')
        return

    src = add_prefix(src_dir, files)
    dest = add_prefix(dest_dir, files)
    n = len(src)
    overwrite = [False for i in range(n)]
    create = [False for i in range(n)]
    skip = [False for i in range(n)]
    dest_exists = [False for i in range(n)]
    color = theme(theme_name.lower())

    if not os.path.isdir(dest_dir) and len(dest_dir) > 0 and not to_remote:

        create = [True for i in range(n)]

    elif check_rsync is not None:

        tmp = diff(
            source_dir = src_dir if to_remote else hostname + ":" + src_dir,
            dest_dir = hostname + ":" + dest_dir if to_remote else dest_dir,
            tempfilename = check_rsync,
            files = files,
            checksum = checksum,
            force = force)

        skip = tmp['skip']
        create = tmp['create']
        overwrite = tmp['overwrite']

    else:

        if checksum == True:
            src_checksums = get(src, yaml_hostinfo_src, progress=not quiet)
            dest_checksums = get(dest, yaml_hostinfo_dest, progress=not quiet)

        if to_remote:
            if yaml_hostinfo_dest:
                f = read(yaml_hostinfo_dest)['files']
                for i in range(n):
                    if files[i] in f:
                        dest_exists[i] = True
        elif not to_remote:
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
    pcreate = not ((noverwrite > 0 and ncreate > 100) or ncreate > 300) or print_all
    pskip = (nskip <= 100) or print_all
    pcreate_message = ' (not printed)' if not pcreate else ''
    pskip_message = ' (not printed)' if not pskip else ''

    overview = []
    if ncreate > 0:
        overview += [String('create (->): {0:d}{1:s}'.format(ncreate, pcreate_message), color=color['new']).format()]
    if noverwrite > 0:
        overview += [String('overwrite (=>): {0:d}'.format(noverwrite), color=color['overwrite']).format()]
    if nskip > 0:
        overview += [String('skip (==): {0:d}{1:s}'.format(nskip, pskip_message), color=color['skip']).format()]

    summary = []
    if to_remote:
        summary += ['- to host        : ' + host]
        summary += ['- source (local) : ' + os.path.normpath(src_dir)]
        summary += ['- dest (remote)  : ' + os.path.normpath(dest_dir)]
    else:
        summary += ['- from host       : ' + host]
        summary += ['- source (remote) : ' + os.path.normpath(src_dir)]
        summary += ['- dest (local)    : ' + os.path.normpath(dest_dir)]
    summary += ['- ' + ', '.join(overview)]

    if ncreate + noverwrite <= 100 and print_summary:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    if print_details:
        for i in range(n):
            if create[i] and pcreate:
                print('{0:s} {1:s} {2:s}'.format(
                    String(files[i], width=l, color=color['bright']).format(),
                    String('->', color=color['bright']).format(),
                    String(files[i], color=color['new']).format()
                ))
            elif skip[i] and pskip:
                print('{0:s} {1:s} {2:s}'.format(
                    String(files[i], width=l, color=color['skip']).format(),
                    String('==', color=color['skip']).format(),
                    String(files[i], color=color['skip']).format()
                ))
            elif overwrite[i]:
                print('{0:s} {1:s} {2:s}'.format(
                    String(files[i], width=l, color=color['bright']).format(),
                    String('=>', color=color['bright']).format(),
                    String(files[i], color=color['overwrite']).format()
                ))

    if ncreate + noverwrite > 100 and print_summary:
        print('-----')
        print('\n'.join(summary))
        print('-----')

    if all(skip):
        return 0

    if not force:
        if not click.confirm('Proceed?'):
            raise IOError('Cancelled')

    if not to_remote:
        makedirs(list(set([os.path.dirname(i) for i in dest])))

    i = np.argwhere(np.not_equal(skip, True)).ravel()
    src = np.array(src)[i]
    dest = np.array(dest)[i]
    files = np.array(files)[i]

    if use_rsync:
        dest_dir = dest_dir if len(dest_dir) > 0 else '.'
        src_dir = src_dir if len(src_dir) > 0 else '.'
        return copy_function(host, src_dir, dest_dir, tempfilename, files, force, verbose, not quiet)

    pbar = tqdm.trange(len(files), disable=quiet)
    for i in pbar:
        pbar.set_description(files[i])
        copy_function(host, src[i], dest[i], verbose)
