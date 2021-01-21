# shelephant

[![CI](https://github.com/tdegeus/shelephant/workflows/CI/badge.svg)](https://github.com/tdegeus/shelephant/actions)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/shelephant.svg)](https://anaconda.org/conda-forge/shelephant)
[![PyPi release](https://img.shields.io/pypi/v/shelephant.svg)](https://pypi.org/project/shelephant/)


Command-line arguments with a memory (stored in YAML-files).

<!-- MarkdownTOC -->

- [Overview](#overview)
    - [Hallmark feature: Copy with restart](#hallmark-feature-copy-with-restart)
    - [Command-line tools](#command-line-tools)
        - [File information](#file-information)
        - [File operations](#file-operations)
        - [YAML file operations](#yaml-file-operations)
- [Disclaimer](#disclaimer)
- [Getting shelephant](#getting-shelephant)
    - [Using conda](#using-conda)
    - [Using PyPi](#using-pypi)
    - [From source](#from-source)
- [Detailed examples](#detailed-examples)
    - [Get files from remote, allowing restarts](#get-files-from-remote-allowing-restarts)
        - [Avoid recomputing checksums](#avoid-recomputing-checksums)
    - [Send files to host](#send-files-to-host)
        - [Basic copy](#basic-copy)
        - [Restart](#restart)
- [Change-log](#change-log)
    - [v0.11.0](#v0110)
    - [v0.10.0](#v0100)
    - [v0.9.0](#v090)
    - [v0.8.1](#v081)
    - [v0.8.0](#v080)
    - [v0.7.0](#v070)
    - [v0.6.0](#v060)
    - [v0.5.0](#v050)
    - [v0.4.0](#v040)

<!-- /MarkdownTOC -->

# Overview

## Hallmark feature: Copy with restart

*shelephant* presents you with a way to copy files (from a remote, using SSH) in two steps:
1.  Collect a list of files that should be copied in a YAML-file, 
    allowing you to **review and customise** the copy operation 
    (e.g. by *changing the order* and making last-minute manual changes).
2.  Perform the copy, efficiently skipping files that are identical.

Typical workflow:

```bash
# Collect files to copy & compute their checksum (e.g. on remote system)
# - creates "shelephant_dump.yaml"
shelephant_dump *.hdf5
# - reads "shelephant_dump.yaml" 
# - creates "shelephant_checksum.yaml"
shelephant_checksum 

# Combine all needed info (locally)
# - reads "shelephant_dump.yaml" and "shelephant_checksum.yaml"
# - creates "shelephant_hostinfo.yaml"
shelephant_hostinfo --host myhost --prefix /some/path --files --checksum

# Copy from remote (can be restarted and any time, existing files are skipped)
# - reads "shelephant_hostinfo.yaml"
shelephant_get
```

>   *   The filenames can be customised.
>   *   To copy *to* a remote system use `shelephant_send`.
>   *   Get details in the help of the respective commands, e.g. `shelephant_dump --help`.
>   *   *shelephant* works for both local as remote copy actions.

## Command-line tools

### File information

*   `shelephant_dump`: list filenames in a YAML file.
*   `shelephant_checksum`: get the checksums of files listed in a YAML file.
*   `shelephant_hostinfo`: collect host information (from a remote system).

### File operations

*   `shelephant_get`: copy from remote, based on earlier stored information.
*   `shelephant_send`: copy to remote, based on earlier stored information.
*   `shelephant_rm`: remove files listed in a YAML file.
*   `shelephant_cp`: copy files listed in a YAML file.
*   `shelephant_mv`: move files listed in a YAML file.

### YAML file operations

*   `shelephant_extract`: isolate a (number of) field(s) in a (new) YAML file.
*   `shelephant_merge`: merge two YAML-files.
*   `shelephant_parse`: parse a YAML-files and print to screen.

# Disclaimer

This library is free to use under the [MIT license](https://github.com/tdegeus/shelephant/blob/master/LICENSE). Any additions are very much appreciated, in terms of suggested functionality, code, documentation, testimonials, word-of-mouth advertisement, etc. Bug reports or feature requests can be filed on [GitHub](https://github.com/tdegeus/shelephant). As always, the code comes with no guarantee. None of the developers can be held responsible for possible mistakes.

Download: [.zip file](https://github.com/tdegeus/shelephant/zipball/master) | [.tar.gz file](https://github.com/tdegeus/shelephant/tarball/master).

(c - [MIT](https://github.com/tdegeus/shelephant/blob/master/LICENSE)) T.W.J. de Geus (Tom) | tom@geus.me | www.geus.me | [github.com/tdegeus/shelephant](https://github.com/tdegeus/shelephant)

# Getting shelephant

## Using conda

```bash
conda install -c conda-forge shelephant
```

This will also download and install all necessary dependencies.

## Using PyPi

```bash
pip install shelephant
```

This will also download and install the necessary Python modules.

## From source

```bash
# Download shelephant
git checkout https://github.com/tdegeus/shelephant.git
cd shelephant

# Install
python -m pip install .
```

This will also download and install the necessary Python modules.


# Detailed examples

## Get files from remote, allowing restarts

Suppose that we want to copy all `*.txt` files
from a certain directory `/path/where/files/are/stored` on a remote host  `hostname`.

First step, collect information *on the host*:

```bash
# connect to the host
ssh hostname

# go the relevant location at the host
cd "/path/where/files/are/stored/on/remote"

# list files to copy 
shelephant_dump -o files_to_copy.yaml *.txt

# optional but useful, get the checksum of the files to copy 
shelephant_checksum -o files_checksum.yaml files_to_copy.yaml 

# disconnect
exit # or press Ctrl + D
```

Second step, copy files to the *local system*, collecting everything in a single place:

```bash
# go to the relevant location on the local system
# (often this is new directory)
cd "/path/where/to/copy/to"

# get the file-information compiled on the host 
# and store in a (temporary) local file
# note that all paths are on the remote system, 
# and that they are now copied using secure-copy (scp)
shelephant_hostinfo \ 
    -o remote_info.yaml \ 
    --host "hostname" \ 
    --prefix "/path/where/files/are/stored/on/remote" \  
    --files "files_to_copy.yaml " \
    --checksum "files_checksum.yaml"

# finally, get the files using secure copy
# (the files are stored relative to the path of 'remote_info.yaml',
# identically to how they are relative to 'files_to_copy.yaml' on remote)
shelephant_get remote_info.yaml
```

>   If you use the default filenames for `shelephant_dump` (`shelephant_dump.yaml`) and 
>   `shelephant_checksum` (`shelephant_checksum.yaml`) remotely, 
>   you can also specify `--files` and `--checksum` without an argument.

An interesting benefit that derives from having computed the checksums on the host,
is that `shelephant_get` can be stopped and restarted:
**only files that do not exist locally, or that were only partially copied 
(whose checksum does not match the remotely computed checksum), will be copied;
all fully copied files will be skipped**.

Let's further illustrate with a complete example. On the host, suppose that we have
```none
/path/where/files/are/stored/on/remote
- foo.txt
- bar.txt
```

This will give, `files_to_copy.yaml`:

```yaml
- foo.txt
- bar.txt
```
`files_checksum.yaml` (for example):

```yaml
- 2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
- fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9
```

This information will be collected to `remote_info.yaml`
```
host: hostname
root: /path/where/files/are/stored/on/remote
files:
    - foo.txt
    - bar.txt
checksum:
    - 2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
    - fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9
```

`shelephant_get` will now copy `foo.txt` and `bar.txt` relative to the directory of 
`remote_info.yaml` 
(in this case in the same folder as `remote_info.yaml`).
It will skip any files whose filename and checksum match to target ones.

### Avoid recomputing checksums

Suppose that we want to restart multiple times, or that we
update the files present on the remote after copying them initially. 
In that case, we can use previously computed
checksums to avoid recomputing them
(which can be costly for large files).

First step, update information *on the host*:

```bash
# connect to the host
ssh hostname

# go the relevant location at the host
cd "/path/where/files/are/stored/on/remote"

# collect the previously computed information
shelephant_hostinfo -o precomputed_checksums.yaml -f files_to_copy.yaml -c files_checksum.yaml

# list files to copy 
shelephant_dump -o files_to_copy.yaml *.txt

# get the checksum of the files to copy, where possible reading precomputed values
shelephant_checksum -o files_checksum.yaml files_to_copy.yaml -l precomputed_checksums.yaml

# disconnect
exit # or press Ctrl + D
```

Second step, copy files to the *local system*, collecting everything in a single place:

```bash
# go to the relevant location on the local system
# (often this is new directory)
cd "/path/where/to/copy/to"

# collect the previously computed information
shelephant_hostinfo -o precomputed_checksums.yaml -f files_present.yaml -c files_checksum.yaml

# list files currently present locally
shelephant_dump -o files_present.yaml *.txt

# get the checksum of the files to copy, where possible reading precomputed values
shelephant_checksum -o files_checksum.yaml files_present.yaml -l precomputed_checksums.yaml

# combine local files and checksums
shelephant_hostinfo -o precomputed_checksums.yaml -f files_present.yaml -c files_checksum.yaml

# get the file-information compiled on the host [as before]
shelephant_hostinfo \ 
    -o remote_info.yaml \ 
    --host "hostname" \ 
    --prefix "/path/where/files/are/stored/on/remote" \  
    --files "files_to_copy.yaml " \
    --checksum "files_checksum.yaml" 

# get the files using secure copy
# use the precomputed checksums instead of computing them
shelephant_get remote_info.yaml --local "precomputed_checksums.yaml"
```

## Send files to host

### Basic copy

Suppose that we want to copy all `*.txt` files
from a certain local directory `/path/where/files/are/stored/locally`, 
to a remote host `hostname`.

First, we will collect information *locally*:

```bash
# go the relevant location (locally)
cd /path/where/files/are/stored/locally

# list files to copy 
shelephant_dump -o files_to_copy.yaml *.txt
```

Then, we will specify some basic information about the host

```bash
# specify basic information about the host
# and store in a (temporary) local file
shelephant_hostinfo \ 
    -o remote_info.yaml \ 
    --host "hostname" \ 
    --prefix "/path/where/to/copy/to/on/remote" \  
```

Now we can copy the files:
```bash
shelephant_send files_to_copy.yaml remote_info.yaml
```

### Restart

Suppose that copying was interrupted before completing. 
We can avoid recopying by again using the checksums. 
We therefore need to know which files are already present remotely
and which checksum they have. 
Thereto:

```bash
# connect to the host
ssh hostname

# go the relevant location at the host
cd "/path/where/to/copy/to/on/remote"

# list files to copy 
shelephant_dump -o files_to_copy.yaml *.txt

# get the checksum of the files to copy 
shelephant_checksum -o files_checksum.yaml files_to_copy.yaml 

# disconnect
exit # or press Ctrl + D
```

Now we will complement the basic host-info:
```bash
shelephant_hostinfo \ 
    -o remote_info.yaml \ 
    --host "hostname" \ 
    --prefix "/path/where/to/copy/to/on/remote" \  
    --files "files_to_copy.yaml " \
    --checksum "files_checksum.yaml"
```

And restart the partial copy:
```bash
shelephant_send files_to_copy.yaml remote_info.yaml
```

# Change-log

## v0.11.0

*    Adding test to checkout for correct order of pre-computed checksums
*    Bugfix in reordering of pre-computed checksum
*    Copy functions: skipping empty input
*    Bugfix in error print
*    Style updates tests
*    Copy functions: allow force-print details. Further auto-truncation otherwise
*    Copy functions: bugfix in progress bar
*    Bugfix in matching checksums

## v0.10.0

*    Copy functions: Skip printing created files if there are also overwritten files
*    Fixing tests
*    Copy functions: Adding option to force print details
*    YamlDump: create directory if needed
*    Adding progress-bar to copy operations
*    Adding progress-bar to checksums
*    GetChecksums: enhance efficiency in reading from precomputed checksums

## v0.9.0

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

## v0.8.1

*   Bugfix in directory creation. Switching to central function.

## v0.8.0

*    Adding "shelephant_cp" and "shelephant_mv"
*    Adding append option to "shelephant_dump"
*    Adding squash option to "shelephant_extract"

## v0.7.0

*   Using default sources in `shelephant_send` and `shelephant_rm`.
*   Various updates to make the help more readable.
*   Adding short options `shelephant_hostinfo`.

## v0.6.0

*   Adding `shelephant_parse`.

## v0.5.0

*   shelephant_get: accepting default source-file

## v0.4.0

*   shelephant_hostinfo: allow update of existing remote file
*   shelephant_get: fixing counter
*   shelephant_checksum: accepting default source-file
*   Checksum: updating chunk size

