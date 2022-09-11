
**********
Change-log
**********

v0.18.0
=======

API changes
-----------

*   Making rsync default to check difference (removes ``--check-rsync`` option).
    To get the old default use ``--check-manual``.

*   ``shelephant.rsync``: removing ``tempfilename`` and ``force`` options.
    The temporary file is now internal, with the proper clean-up.

*   ``shelephant.rsync``: removing ``rsync`` option. Use ``rsync_path`` instead.

*   ``shelephant_dump``: adding ``--cwd`` option.

v0.17.5
=======

*   rsync: interpreting cryptic both in send and receive mode
*   [CI] Minor style update

v0.17.4
=======

*   Fixing bug in command-line parsing of ``shelephant_send``: defaults were not selected.

v0.17.3
=======

*   Fixing typos

v0.17.2
=======

*   Normalising paths in copy functions.

v0.17.1
=======

*   Documentation updates
*   (Re-)Account for non-existing destination for copying from remote

v0.17.0
=======

*   The Python API is now subdivided in namespaces and only lower-case letters are used.

v0.16.0
=======

*   Allow use of rsync to check file difference
*   Internal simplification: ``Rsync`` combines implementation of
    ``RsyncToRemote`` and ``RsyncFromRemote``.
*   Minor bugfixes

v0.15.0
=======

*   Switching to argparse
*   Bugfix: incorrectly detecting current directory as non-existent
*   Adding convenience methods

v0.14.4
=======

*   rsync: wrapping progress-bar also for old versions of rsync
*   Using MakeDirs in ShelephantCopySSH

v0.14.3
=======

*   Versioning: using setuptools_scm -> include git commit hash (#71)

v0.14.2
=======

*   Bugfix: empty path given to rsync.

v0.14.1
=======

*   Copy functions: improving error message
*   Copy functions: creating destination directories
*   Using assertions to simplify the code

v0.14.0
=======

*   Adding badges to readme
*   Making several functions private. Adding summary to docs.
*   Adding readthedocs environment
*   Adding documentation
*   Adding size progress to send/get
*   send/get: using rsync as backend (for speed)
*   Copy functions: preserve metadata

v0.13.0
=======

*   shelephant_hostinfo: add option to remove paths
*   copy functions: add progress-bar for reading checksums

v0.12.0
=======

*   Improving exception handling: removing internal sys.exit(1),
    replacing them by try...except wrappers
*   shelephant_hostinfo: default to empty file list (#58)
*   Minor bugfix

v0.11.0
=======

*    Adding test to checkout for correct order of pre-computed checksums
*    Bugfix in reordering of pre-computed checksum
*    Copy functions: skipping empty input
*    Bugfix in error print
*    Style updates tests
*    Copy functions: allow force-print details. Further auto-truncation otherwise
*    Copy functions: bugfix in progress bar
*    Bugfix in matching checksums

v0.10.0
=======

*    Copy functions: Skip printing created files if there are also overwritten files
*    Fixing tests
*    Copy functions: Adding option to force print details
*    YamlDump: create directory if needed
*    Adding progress-bar to copy operations
*    Adding progress-bar to checksums
*    GetChecksums: enhance efficiency in reading from precomputed checksums

v0.9.0
======

*    Changing namespace Python module: `shelephant.cli` -> `shelephant`
*    `shelephant_checksum`: Allow reuse of pre-computed checksums
*    API change: `shelephant_remote` -> `shelephant_hostinfo`
*    Centralizing implementation `shelephant_get`
*    Updating ssh tests
*    Centralizing implementation `shelephant_send`
*    Implementation simplifications
*    `shelephant_send`: allow use of pre-computed checksum
*    Updating counter in copy scripts
*    Large output: summarizing skipped files
*    Copy: Adding assertion that source must exist
*    `shelephant_get`: Adding possibility to use local checksums for
*    Updating change-log

v0.8.1
======

*   Bugfix in directory creation. Switching to central function.

v0.8.0
======

*    Adding "shelephant_cp" and "shelephant_mv"
*    Adding append option to "shelephant_dump"
*    Adding squash option to "shelephant_extract"

v0.7.0
======

*   Using default sources in `shelephant_send` and `shelephant_rm`.
*   Various updates to make the help more readable.
*   Adding short options `shelephant_hostinfo`.

v0.6.0
======

*   Adding `shelephant_parse`.

v0.5.0
======

*   shelephant_get: accepting default source-file

v0.4.0
======

*   shelephant_hostinfo: allow update of existing remote file
*   shelephant_get: fixing counter
*   shelephant_checksum: accepting default source-file
*   Checksum: updating chunk size
