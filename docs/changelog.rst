
**********
Change-log
**********

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
