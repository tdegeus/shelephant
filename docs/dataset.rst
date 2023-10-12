
******************
Dataset management
******************

The idea is that you will have a "dataset" directory that has symbolic links to one of the available "storage" locations, instead of storing the data itself.
This allows for distributed storage and/or storage of multiple copies of the same data.

*   Reading and modifying files in the "dataset" directory will be done as normal.
    This changes the corresponding file in the currently used "storage" location, but none of the other copies.

*   Creating a new file in the "dataset" directory will be an 'unmanaged' file.
    As such it will not exist in any of the "storage" locations.
    However, it will be a regular file in the "dataset" directory.
    It is up to the user to decide whether to add it to (one of) the "storage" location(s).

There are methods to copy or move files to or between the "storage" locations.

.. tip::

    The two key reasons to use this tool are:

    1.  To keep an overview of a the dataset's structure also if some storage locations may not be available part of the time.

    2.  To keep a track of where multiple copies of files are and to get an overview of which copies might be outdated.
        In addition, you can easily 'enforce' multiple copies.

Basic usage
===========

Dataset directory
-----------------

You will start the dataset by:

.. code-block:: bash

    cd /path/to/my/dataset
    shelephant init

This creates a directory:

.. code-block:: bash

    .shelephant

(i.e. ``/path/to/my/dataset/.shelephant``) and two files (and two empty directories and a dead symbolic link, more below):

.. code-block:: bash

    .shelephant/symlinks.yaml  # symlinks created by shelephant (initially empty)
    .shelephant/storage.yaml   # priority of storage locations (initially "- here")

.. note::

    You are allowed to use any name that you like to indicate storage locations, except ``here`` that is reserved for the dataset directory itself, and ``all`` and ``any`` that are keywords to select indicate a generic selection of datasets.

Adding existing data
--------------------

Suppose that you have existing data in some location ``/path/to/my/data`` that you want to add to the dataset.
You can do this by:

.. code-block:: bash

    shelephant add "laptop" "/path/to/my/data" --rglob "*.h5" --skip "bak.*" --skip "\..*"

This will:

1.  Create:

    .. code-block:: bash

        .shelephant/storage/laptop.yaml

    that contains information which files to 'manage' from the storage location, as follows:

    .. code-block:: yaml

        root: /path/to/my/data  # may be relative
        search:
            - rglob: '*.h5'             # run as pathlib.Path(root).rglob(PATTERN)
              skip: ['\..*, 'bak.*']    # ignore path(s) (Python regex)

    .. tip::

        Don't hesitate to modify this file by hand.
        For example, you may want to have multiple "search" entries. For example:

        .. code-block:: yaml

            root: /path/to/my/data  # may be relative
            search:
                - rglob: '*.h5'
                  skip: ['\..*, 'bak.*']
                - rglob: '*.yaml'
                  skip: ['\..*, 'bak.*', '[\.]?(shelephant)(.*)']

    .. note::

        "search" is not mandatory but highly recommended.
        Instead you can rely on a "dump" file in the source directory (see ``shelephant_dump``).
        If you specify neither "search" nor "dump" you have to specify the managed files by hand (see below).

2.  Update the available storage locations in

    .. code-block:: bash

        .shelephant/storage.yaml

    which now contains:

    .. code-block:: yaml

        - here
        - laptop

3.  Create a symbolic link to the storage location

    .. code-block:: bash

        .shelephant/data/laptop -> /path/to/my/data

4.  Determine the current state and update

    .. code-block:: bash

        .shelephant/storage/laptop.yaml

    which could be:

    .. code-block:: yaml

        root: /path/to/my/data  # may be relative
        search:
            - rglob: '*.h5'             # run as pathlib.Path(root).rglob(PATTERN)
              skip: ['\..*, 'bak.*']    # ignore path(s) (Python regex)
        files:
            - path: a.h5
              sha256: bbbd486f44cba693a77d216709631c2c3139b1e7e523ff1fcced2100c4a19e59
              size: 11559
              mtime: 12345.567
            - path: mydir/b.h5
              sha256: 3cff1315981715840ed1df9180cd2af82a65b6b1bbec7793770d36ad0fbc2816
              size: 1757
              mtime: 12346.897

    .. note::

        Computing the checksum ("sha256") will take a bit of time.
        You can use ``--shallow`` to skip this.
        However, this will degrade the functionality of *shelephant* and the integrity of the dataset.

    .. note::

        The modification time (``mtime``, in seconds from epoch) and size are used to estimate is the *sha256* might have changed when you update the dataset.

    .. warning::

        This file is assumed to reflect the state of the storage location.
        This is not automatically checked.
        You are responsible to call ``shelephant update all`` or ``shelephant update laptop`` when needed (or make modifications by hand).

5.  Add files to the dataset directory by creating symbolic links to the storage location:

    .. code-block:: bash

        a.h5 -> .shelephant/data/laptop/a.h5
        mydir/b.h5 -> ../.shelephant/data/laptop/mydir/b.h5

    .. note::

        *shelephant* will keep track of which symbolic links it created in ``.shelephant/symlinks.yaml``:

        .. code-block:: yaml

            - path: a.h5
              storage: laptop
            - path: mydir/b.h5
              storage: laptop

.. note::

    If you manually add ``.shelephant/storage/{name}.yaml`` be sure to call:

    .. code-block:: bash

        shelephant update --base-link {name}

    to update the internal link ``.shelephant/data/{name}`` to the data.
    This command will also add ``{name}`` to the end of ``.shelephant/storage.yaml`` if needed (manually update the order if needed).

Adding secondary storage
------------------------

Suppose that your dataset is partly available elsewhere (can also be an external source like a USB drive, a network storage, an SSH host, ...).
You then want the dataset directory to reflect the full state of the dataset, even though it is physically stored in different locations.
You do this by adding another storage location.
Let us assume that you have a USB drive mounted at ``/media/myusb``.
Then:

.. code-block:: bash

    shelephant add "usb" "/media/myusb/mydata" --rglob "*.h5" --skip "\..*"

This will:

1.  Create:

    .. code-block:: bash

        .shelephant/storage/usb.yaml

    with (for example):

    .. code-block:: yaml

        root: /media/myusb/mydata
        search:
            - rglob: '*.h5'
              skip: '\..*'
        files:
            - path: a.h5
              sha256: bbbd486f44cba693a77d216709631c2c3139b1e7e523ff1fcced2100c4a19e59
              size: 11559
              mtime: 12347.123
            - path: mydir/c.h5
              sha256: 6eaf422f26a81854a230b80fd18aaef7e8d94d661485bd2e97e695b9dce7bf7f
              size: 4584
              mtime: 12348.465

    .. note::

        Note how the *sha256* is used to check equality.
        *size* and *mtime* are merely used to signal the need to update *sha256*.
        They thus matter on the relevant storage location only.

2.  Update the available storage locations in

    .. code-block:: bash

        .shelephant/storage.yaml

    to

    .. code-block:: yaml

        - here
        - laptop
        - usb

3.  Create a symbolic link to the storage location

    .. code-block:: bash

        .shelephant/data/usb -> /media/myusb/mydata

5.  Update the dataset directory.

    In this example, both "laptop" and "usb" contain an identical file ``a.h5``, whereby ``.shelephant/storage.yaml`` marks "laptop" as preferential (as it is listed first in ``.shelephant/storage.yaml``).
    Furthermore, "laptop" contains a file that "usb" does not have and vice versa.
    The "dataset" will now have all the files:

    .. code-block:: bash

        a.h5 -> .shelephant/data/laptop/a.h5
        mydir/b.h5 -> ../.shelephant/data/laptop/mydir/b.h5
        mydir/c.h5 -> ../.shelephant/data/usb/mydir/b.h5

    .. note::

        ``.shelephant/symlinks.yaml`` is now:

        .. code-block:: yaml

            - path: a.h5
              storage: laptop
            - path: mydir/b.h5
              storage: laptop
            - mydir/c.h5
              storage: usb

    .. warning::

        It is important to emphasise that *shelephant* will create links for the full dataset.
        A file will point to the first available location in the order specified in ``.shelephant/storage.yaml`` (that you can customise to your needs).
        **This does not guarantee that it is the newest version of the file, you are responsible for managing that.**

        If none of the storage locations is available, *shelephant* will create links to ``.shelephant/unavailable``.
        For example:

        .. code-block:: bash

            - d.h5 -> .shelephant/unavailable/d.h5

        This is a dangling link which you cannot use, but is there to help you keep track of the full dataset.

.. tip::

    If you store a subdirectory of a dataset somewhere else, you can avoid storing the structure.
    For example, as dataset as follows:

    .. code-block:: none

        |-- a.h5
        `-- mydir
            |-- b.h5
            `-- c.h5

    where you want to store ``mydir`` on a USB drive. Such that for example ``/mount/usb/mydata`` contains:

    .. code-block:: none

        |-- b.h5
        `-- c.h5

    You can do this by:

    .. code-block:: bash

        shelephant add "usb" "/mount/usb/mydata" --rglob "*.h5" --prefix "mydir"

Keeping the dataset clean
-------------------------

To avoid that you store files in the dataset directory that you intend to store in one/several storage locations, you can add

.. code-block:: bash

    shelephant add "here" --rglob "*.h5" --skip "bak.*"

whereby the name ``"here"`` is specifically reserved for the dataset directory.
This will update:

.. code-block:: bash

    .shelephant/storage/here.yaml

with:

.. code-block:: yaml

    root: ../..
    search:
        - rglob: '*.h5'
        - skip: 'bak.*'

.. note::

    There is no ``files`` entry.
    Instead, the presence of files is searched on the fly if needed.
    Since these are 'unmanaged' files, no checksums are needed.

Running ``shelephant status`` will include lines for 'managed' files that are in the dataset directory but that you intent to have in a storage location.
As an example, let us assume that you create a file ``e.h5`` in the dataset directory.

Getting an overview
===================

status
------

To get an overview use

.. code-block:: bash

    shelephant status

It will output something like:

============== ========== ========== =======
path           in use     ``laptop`` ``usb``
============== ========== ========== =======
``a.h5``       ``laptop`` ``==``     ``==``
``mydir/b.h5`` ``laptop`` ``==``     ``x``
``mydir/c.h5`` ``usb``    ``x``      ``==``
``e.h5``       ``here``   ``x``      ``x``
============== ========== ========== =======

with columns:

1.  The files (symlinks) in the dataset directory.
2.  The storage location currently in use.
3.  The status of the file in the storage locations (one column per storage location; only shown if there is more than one storage location).

.. note::

    To limit the output to two columns use ``--short``.

The status (column 3, 4, ...) can be

*   ``==``: the file is the same in all locations where it is present.
*   ``1``, ``2``, ...: different copies of the file exist; the same number means that the files are the same.
    The lower number, the newer the file likely is.
*   ``x``: the file is not available in that location.
*   ``?``: the file is available in that location but the ``sha256`` is unknown.

.. note::

    Even though ``e.h5`` is not a symbolic link, it is included in the overview, because it was marked as a type of file that you intent to store in a storage location.

There are several filters (that can be combined!):

==================== ===============================================================
option               description
==================== ===============================================================
``--copies`` n       specific number of copies
``--ne``             more than one copy, at least one not equal (``1``, ``2``, ...)
``--eq``             more than one copy, all equal (``==``)
``--na``             currently not available in any connected storage location
``--unknown``        sha256 unknown (``?``)
``--in-use`` NAME    list files used from a specific storage location
==================== ===============================================================

``--output``
------------

If you want to do further processing, you can get a list of files in a yaml-file:

.. code-block:: bash

    shelephant status [filters] --output myfiles.yaml

``--copy``
----------

To copy the selected files to a storage location or between storage locations, use:

.. code-block:: bash

    shelephant status [filters] --copy source destination

where ``source`` and ``destination`` are storage locations (e.g. "here", "laptop", "usb", ...).

Getting updates
===============

First suppose that you have changed a storage location by 'hand'.
For example, you added some files to ``.shelephant/storage/usb.yaml``.
Or, you have removed ``.shelephant/storage/usb.yaml`` and removed "usb" from ``.shelephant/storage.yaml`` (which we will assume below).
To update the symbolic links, run:

.. code-block:: bash

    shelephant update

This will add new links if needed, and remove all links that are not part of any storage location (and update ``.shelephant/symlinks.yaml``).
For this example, removing "usb" will amount to removing the symbolic link ``mydir/c.h5``.

.. note::

    Nothing changes to the storage location, *shelephant* has no authority over it.

.. note::

    *shelephant* has no history or undo.
    Not that this is a problem!
    The storage itself is never touched.

``all``
-------

.. code-block:: bash

    shelephant update all

will update every file in ``.shelephant/storage`` (if the storage location is available).
It will also update the symbolic links.

You can also update a specific location:

.. code-block:: bash

    shelephant update usb

``--shallow``
-------------

.. code-block:: bash

    shelephant update --shallow

will only check if there are new files or if files are removed.
No checksums are recomputed.

Copying files
=============

To copy files to a storage location, use:

.. code-block:: bash

    shelephant cp source destination path [path ...]

Likewise for moving files:

.. code-block:: bash

    shelephant mv source destination path [path ...]

where ``source`` and ``destination`` are storage locations (e.g. "here", "laptop", "usb", ...).

Advanced
========

SSH host
--------

If you add an SSH host:

.. code-block:: bash

    shelephant add "cluster" "/path/on/remote" --rglob "*.h5" --ssh "user@host"

*shelephant* will search for the files on the remote host and compute their checksums there.
Depending on the priority of the storage locations, it will create 'dead' symbolic links.
This allows you to keep an overview of the structure of the dataset and of the location and number of copies of each file (but you cannot use the files locally).

If you want to use the remote files locally, you need on *sshfs* mount.
If you mount the remote location you can either add it is a local storage location (just like any local directory or removable storage location), or you can indicate that it is a remote location.
For the latter do

.. code-block:: bash

    shelephant add "cluster" "/path/on/remote" --rglob "*.h5" --ssh "user@host" --mount /local/mount

This will create the symbolic links to the relevant locations in ``/local/mount``, but it will compute the checksums directly on the remote host.
The additional benefit is that if the mount is unavailable, the behaviour is the same as for any SSH host.

Updates on remote
-----------------

You can also update the database of a storage location on the storage location itself.
This is useful to speedup updating a large database on a remote host, or for example if you have limited connectivity to a remote host or if you want to close the connection while computing checksums.
The simplest you can do is:

1.  Copy the database entry of a storage location:

    .. code-block:: bash

        shelephant cp here remote -ex .shelephant/storage/remote.yaml

    .. note::

        -   ``-e`` (``--exists``) is needed if ``.shelephant/storage/remote.yaml`` is not part of the dataset (recommended).
        -   ``-x`` (``--no-update``) if then needed to prevent ``.shelephant/storage/remote.yaml`` being added to the dataset (recommended).

2.  **On the storage location:**

    a.  Run

        .. code-block:: bash

            shelephant lock remote

    b.  Run (whenever you need):

        .. code-block:: bash

            shelephant update

3.  Receive the updates (from the dataset root):

    .. code-block:: bash

        shelephant cp remote here -ex .shelephant/storage/remote.yaml
        shelephant update

Updates with git
----------------

We now want to use a central storage (e.g. GitHub) to send updates about the dataset.

.. code-block:: bash

    cd /path/to/my/dataset # or any subdirectory
    shelephant git init    # simply run from "/path/to/my/dataset/.shelephant" (same below)
    shelephant git add -A
    shelephant git commit -m "Initial commit"
    shelephant git remote add origin <REMOTE_URL>
    shelephant git push -u origin main

Now, on one of the storage locations (e.g. "usb") we are going to clone the repository:

.. code-block:: bash

    cd /media/myusb/mydata
    git clone <REMOTE_URL> .shelephant

.. note::

    We can not yet use the *shelephant* proxy for git yet because there is no ``.shelephant`` folder yet.

**Important:** we will now tell shelephant that this is a storage location (such that symbolic links are not created), and which one it is:

.. code-block:: bash

    shelephant lock "usb"

Calling

.. code-block:: bash

    shelephant update

will now read ``.shelephant/storage/usb.yaml`` and update the list of files according to ``"search"``.
If ``"search"`` is not specified, only no longer existing files are removed from ``.shelephant/state/usb.yaml``, but nothing is added.
Furthermore, it will update all metadata ("sha256", "size", "mtime") to the present values.

The lock file is relevant only per storage location.
It should thus not be part of the dataset's history.
Therefore, it is suggested to add it to ``.gitignore``:

.. code-block:: bash

    echo "lock.txt" >> .shelephant/.gitignore
    shelephant git add .gitignore
    shelephant git commit -m "Ignore lock file"

To propagate this to the central storage we do:

.. code-block:: bash

    shelephant git add -A
    shelephant git commit -m "Update state of usb-drive"
    shelephant git push

Now you can get the updates on your laptop (even if the two systems would not have any direct connection):

.. code-block:: bash

    cd /path/to/my/dataset
    shelephant git pull
