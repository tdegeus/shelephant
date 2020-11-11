# shelephant

Command-line arguments with a memory (stored in YAML-files).

# Features

## Get files from host, allowing restarts

Suppose that we want to copy all `*.txt` files
from a certain directory `/path/where/files/are/stored` on a remote host, 
with hostname simply `hostname`.

First step, collect information *on the host*:

```bash
# connect to the host
ssh hostname

# go the relevant location at the host
cd /path/where/files/are/stored

# list files to copy 
shelephant_dump -o files_to_copy.yaml *.txt

# optional but useful, get the checksum of the files to copy 
shelephant_hash -o files_checksum.yaml files_to_copy.yaml 

# disconnect
exit # or press Ctrl + D
```

Second step, copy files to the *local system*:

```bash
# go to the relevant location on the local system
# (often this is new directory)
cd /path/where/to/copy/to

# get the file-information compiled on the host 
# and store in a (temporary) local file
shelephant_hostinfo \ 
    -o hostinfo.yaml \ 
    --host "hostname" \ 
    --prefix "/path/where/files/are/stored" \  
    --paths "files_to_copy.yaml " \
    --hash "files_checksum.yaml"

# finally, get the files
shelephant_get hostinfo.yaml
```

An interesting benefit that derives from having computed the checksums on the host,
is that `shelephant_get` can be stopped and restarted:
**only files that do not exist locally, or that were only partially copied 
(whose checksum does not match the remotely computed checksum), will be copied;
all fully copied files will be skipped**.

Let's illustrate the with an example. On the host, suppose that we have
```none
/path/where/files/are/stored
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

This information will be collected to `hostinfo.yaml`
```
host: hostname
root: /path/where/files/are/stored
files:
    - foo.txt
    - bar.txt
hash:
    - 2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
    - fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9
```
