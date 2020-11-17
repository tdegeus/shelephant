# shelephant

[![CI](https://github.com/tdegeus/shelephant/workflows/CI/badge.svg)](https://github.com/tdegeus/shelephant/actions)

Command-line arguments with a memory (stored in YAML-files).

# Features

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
shelephant_remote \ 
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
>   you can also specify `--files` and ``--checksum` without an argument.

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
shelephant_remote \ 
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
shelephant_remote \ 
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


