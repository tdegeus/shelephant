Copying files
=============

Locally
-------

1.  List the files that you would like to have copied.
    For example:

    .. code-block:: bash

        cd /path/to/your/files
        shelephant_dump *.h5

    This creates a file ``shelephant_dump.yaml`` with a list of files:

    .. code-block:: yaml

        - file1.h5
        - file2.h5
        - file3.h5

    .. note::

        The filenames are relative to ``shelephant_dump.yaml``.

2.  Copy all files to some destination:

    .. code-block:: bash

        shelephant_cp shelephant_dump.yaml /path/to/destination

    This copies:

    .. code-block:: bash

        file1.h5 -> /path/to/destination/file1.h5
        file2.h5 -> /path/to/destination/file2.h5
        file3.h5 -> /path/to/destination/file3.h5

    .. tip::

        You can
