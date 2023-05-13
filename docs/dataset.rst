
******************
Dataset management
******************

The idea is that you will have a "dataset" directory that instead of storing the data has symbolic links to one of the available "storage" locations.
This allows for distributed storage and/or storage of multiple copies of the same data.

*   Reading and modifying files in the "dataset" directory will be done as normal.
    This changes the corresponding file in the currently used "storage" location, but none of the other copies.

*   Creating a new file in the "dataset" directory will be an 'unmanaged' file.
    As such it will not exist in any of the "storage" locations.
    However, it will be a regular file in the "dataset" directory.
    It is up to the user to decide whether to add it to (one of) the "storage" location(s).

There are methods to copy or move files to or between the "storage" locations.

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

(i.e. ``/path/to/my/dataset/.shelephant``) and two files (that for the moment are empty):

.. code-block:: bash

    .shelephant/symlinks.yaml  # symlinks created by shelephant
    .shelephant/storage.yaml   # priority of storage locations

Adding existing data
--------------------

Suppose that you have existing data in some location ``/path/to/my/data`` that you want to add to the dataset.
You can do this by:

.. code-block:: bash

    shelephant storage "laptop" "/path/to/my/data" --iname ".*h5" --ignore "bak.*"

This will:

1.  Create:

    .. code-block:: bash

        .shelephant/storage/laptop.yaml

    that contains information which files to 'manage' from the storage location, as follows:

    .. code-block:: yaml

        root: /path/to/my/data  # may be relative
        search:
            - iname: # reduce present files to matching name (Python regex)
                - '.*h5'
            - ignore: # ignore files (Python regex)
                - bak.*

    .. note::

        "search" is not mandatory.
        Instead you can specify the managed files by hand (see below).
        However, it is very useful to use "search" to automatically add files to the dataset.

2.  Update the available storage locations in

    .. code-block:: bash

        .shelephant/storage.yaml

    which now contains:

    .. code-block:: yaml

        - laptop

3.  Create a symbolic link to the storage location

    .. code-block:: bash

        .shelephant/data/laptop -> /path/to/my/data

4.  Determine the current state and store it in

    .. code-block:: bash

        .shelephant/state/laptop.yaml

    which could be:

    .. code-block:: yaml

        - path: a.h5
          sha256: bbbd486f44cba693a77d216709631c2c3139b1e7e523ff1fcced2100c4a19e59
          size: 11559
          modified: 2023-01-01 12:34:56 Europe/Zurich
        - path: mydir/b.h5
          sha256: 3cff1315981715840ed1df9180cd2af82a65b6b1bbec7793770d36ad0fbc2816
          size: 1757
          modified: 2023-01-03 23:53:34 Europe/Zurich

    .. note::

        Computing the checksum ("sha256") will take a bit of time.
        You can use ``--shallow`` to skip this.
        However, this will degrade the functionality of *shelephant* and the integrity of the dataset.

    .. warning::

        This file is assumed to reflect the state of the storage location.
        This is not automatically checked.
        You are responsible to call ``shelephant update`` when needed (or make modifications by hand).

5.  Add files to the dataset directory by creating symbolic links to the storage location:

    .. code-block:: bash

        a.h5 -> .shelephant/data/laptop/a.h5
        mydir/b.h5 -> .shelephant/data/laptop/mydir/b.h5

    .. note::

        *shelephant* will keep track of which symbolic links it created in ``.shelephant/symlinks.yaml``:

        .. code-block:: yaml

            - a.h5
            - mydir/b.h5

Adding secondary storage
------------------------

Suppose that your dataset is partly available elsewhere (can also be an external source like a USB drive, a network storage, an SSH host, ...).
You then want the dataset directory to reflect the full state of the dataset, even though it is physically stored in different locations.
You do this by adding another storage location.
Let us assume that you have a USB drive mounted at ``/media/myusb``.
Then:

.. code-block:: bash

    shelephant storage "usb" "/media/myusb/mydata" --iname ".*h5" --ignore "bak.*"

This will:

1.  Create:

    .. code-block:: bash

        .shelephant/storage/usb.yaml

    with:

    .. code-block:: yaml

        root: /media/myusb/mydata
        search:
            - iname:
                - '.*h5'
            - ignore:
                - bak.*

2.  Update the available storage locations in

    .. code-block:: bash

        .shelephant/storage.yaml

    to

    .. code-block:: yaml

        - laptop
        - usb

3.  Create a symbolic link to the storage location

    .. code-block:: bash

        .shelephant/data/usb -> /media/myusb/mydata

4.  Determine the current state in

    .. code-block:: bash

        .shelephant/state/usb.yaml

    to for example:

    .. code-block:: yaml

        - path: a.h5
          sha256: bbbd486f44cba693a77d216709631c2c3139b1e7e523ff1fcced2100c4a19e59
          size: 11559
          modified: 2023-01-05 10:00:00 Europe/Zurich
        - path: mydir/c.h5
          sha256: 6eaf422f26a81854a230b80fd18aaef7e8d94d661485bd2e97e695b9dce7bf7f
          size: 4584
          modified: 2023-01-06 14:53:34 Europe/Zurich

5.  Update the dataset directory.

    In this example, both "laptop" and "usb" contain an identical file ``a.h5``, whereby ``.shelephant/storage.yaml`` marks "laptop" as preferential.
    Furthermore, "laptop" contains a file that "usb" does not have and vice versa.
    The "dataset" will now have all the files:

    .. code-block:: bash

        a.h5 -> .shelephant/data/laptop/a.h5
        mydir/b.h5 -> .shelephant/data/laptop/mydir/b.h5
        mydir/c.h5 -> .shelephant/data/usb/mydir/b.h5

    .. note::

        ``.shelephant/symlinks.yaml`` is now:

        .. code-block:: yaml

            - a.h5
            - mydir/b.h5
            - mydir/c.h5

    .. warning::

        It is important to emphasise that *shelephant* will create links for the full dataset.
        A file will point to the first available location in the order specified in ``.shelephant/storage.yaml`` (that you can customise to your needs).
        **This does not guarantee that it is the newest version of the file, you are responsible for managing that.**

        If none of the storage locations is available, *shelephant* will create links to ``.shelephant/unavailable``.
        For example:

        .. code-block:: bash

            - d.h5 -> .shelephant/unavailable/d.h5

        This is a dangling link which you cannot use, but is there to help you keep track of the full dataset.

Avoiding local storage
----------------------

To avoid storing files in the dataset directory that you want to store in one/several storage locations, you can add

.. code-block:: bash

    shelephant storage "here" shelephant --iname ".*h5" --ignore "bak.*"

whereby the name ``"here"`` is specifically reserved for the dataset directory.
This will create:

.. code-block:: bash

    .shelephant/storage/here.yaml

with:

.. code-block:: yaml

    search:
        - iname:
            - '.*h5'
        - ignore:
            - bak.*

Running ``shelephant status`` will include lines for 'managed' files that are in the dataset directory but that you intent to have in a storage location.
As an example, let us create a file ``e.h5`` in the dataset directory.

Getting an overview
===================

status
------

To get an overview use

.. code-block:: bash

    shelephant status

It will output something like:

============== ========== ========== =======
name           in use     ``laptop`` ``usb``
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
*   ``1``, ``2``, ...: different copies of the file exists; the same number means that the files are the same, whereby the lowest number is likely the newest version.
*   ``x``: the file is not available in that location.
*   ``?``: the file is available in that location but the ``sha256`` is unknown.

.. note::

    Even tough ``e.h5`` is not a symbolic link, it is included in the overview, because it was marked as a type of file that you intent to store in a storage location.

There are several filters (that can be combined!):

==================== ===============================================================
option               description
==================== ===============================================================
``--copies`` n       specific number of copies
``--ne``             more than one copy, at least one not equal (``1``, ``2``, ...)
``--eq``             more than one copy, all equal (``==``)
``--na``             currently not available in any connected storage location
``--unknown``        status unknown (``?``)
``--storage`` NAME   specific storage location
==================== ===============================================================

``--output``
------------

If you want to do further processing, you can get a list of files in a yaml-file:

.. code-block:: bash

    shelephant status [filers] --output myfiles.yaml

``--copy``
----------

To copy the selected files to a storage location or between storage locations, use:

.. code-block:: bash

    shelephant status [filers] --copy source destination

where ``source`` and ``destination`` are storage locations (e.g. "here", "laptop", "usb", ...).

``--move``
----------

To move the selected files to a storage location or from one storage location to another, use:

.. code-block:: bash

    shelephant status [filers] --move source destination

In practice this first copies and then removes the file.

Getting updates
===============

``--prune``
-----------

First suppose that you have changed a storage location by 'hand'.
For example, you added some files to ``.shelephant/storage/usb.yaml``.
Or, you have removed ``.shelephant/storage/usb.yaml`` and removed "usb" from ``.shelephant/storage.yaml`` (which we will assume below).
To update the symbolic links, run:

.. code-block:: bash

    shelephant update --prune

This will add new links if needed, and remove all links that are not part of any storage location (and update ``.shelephant/symlinks.yaml``).
For this example, removing "usb" will amount to removing the symbolic link ``mydir/c.h5``.

.. note::

    Nothing changes to the storage location, *shelephant* has no authority over it.

.. note::

    *shelephant* has no history or undo.
    Not that this is a problem!
    The storage itself is never touched.

``--all``
---------

.. code-block:: bash

    shelephant update --all

will update every file in ``.shelephant/state`` (if it is possible, i.e. if the storage location is available).
It will also update the symbolic links (i.e. it includes ``--prune``).

You can also update a specific location:

.. code-block:: bash

    shelephant update usb --all


``--updated``
-------------

.. code-block:: bash

    shelephant update --updated

will only recompute the checksums on files that have been modified since the last update.
The assertion is done based on the modification time stored in ``.shelephant/state``.
This is not guaranteed to be fully accurate.

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

    shelephant copy source destination path [path ...]

Likewise for moving files:

.. code-block:: bash

    shelephant move source destination path [path ...]

where ``source`` and ``destination`` are storage locations (e.g. "here", "laptop", "usb", ...).

``--temp``
----------

If you want to work on a file without changing *any* of the storage locations, you can make a temporary copy:

.. code-block:: bash

    shelephant copy --temp path [path ...]

Advanced
========

Getting updates by hand
-----------------------

For example:

.. code-block:: bash

    cd /media/myusb/mydata
    shelephant_dump --search /path/to/my/dataset/.shelephant/storage/usb.yaml --output myfiles.yaml --details
    cp myfiles.yaml /path/to/my/dataset/.shelephant/state/usb.yaml

(or any variant to copy).

.. note::

    You could have even done

    .. code-block:: bash

        shelephant_dump ...
        cp myfiles.yaml /path/to/my/dataset/.shelephant/state/usb.yaml

    if "usb" was not yet part of the dataset.
    The minimal you need to do to make things work is:

    1.  Create

        .. code-block:: bash

            .shelephant/storage/usb.yaml

        with at minimal

        .. code-block:: yaml

            root: /media/myusb/mydata

    2.  Edit

        .. code-block:: bash

            .shelephant/storage.yaml

        to

        .. code-block:: yaml

            - laptop
            - usb

    3.  Run

        .. code-block:: bash

            cd /path/to/my/dataset
            shelephant update --prune

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

    We can not use the *shelephant* proxy for git yet because there is no ``.shelephant`` folder yet.

**Important:** we will now tell shelephant that this is a storage location (such that symbolic links are not created), and which one it is:

.. code-block:: bash

    shelephant lock "usb"

Calling

.. code-block:: bash

    shelephant update

will now read ``.shelephant/storage/usb.yaml`` and update the list of files in ``.shelephant/state/usb.yaml`` according to ``"search"``.
If ``"search"`` is not specified, only no longer existing files are removed from ``.shelephant/state/usb.yaml``, but nothing is added.
Furthermore, it will update all metadata ("sha256", "size", "modified", "created") to the present values.
To propagate this to the central storage we do:

.. code-block:: bash

    shelephant git add -A
    shelephant git commit -m "Update state of usb-drive"
    shelephant git push

Now you can get the updates on your laptop (even if the two systems would not have any direct connection):

.. code-block:: bash

    cd /path/to/my/dataset
    shelephant git pull