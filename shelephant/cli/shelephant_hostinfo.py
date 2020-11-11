'''shelephant_hostinfo
    Get files from remote host.
    This program needs the specification which files to get from where on the host,
    specified in host.yaml.
    In addition, if the checksum (computed on the host) is specified, existing local
    files can be skipped.

    The notion of relativity is important. The files in host.yaml are relative to a certain
    directory on the host.
    The files will be stored locally relative to the current working directory.
    In the example below, the files with be copied to:
    - $PWD/foo.txt
    - $PWD/bar.txt
    - $PWD/directory/bar.txt
    To overwrite $PWD you can specify --prefix.

host.yaml:

    working_diectory:
        /path/to/root/of/files/on/host
    files:
        - foo.txt
        - bar.txt
        - directory/foo.txt

Example workflow:

    ssh hostname
    cd /path/to/files
    shelephant_dumppaths *
    shelephant_hash -p "/files" dumppaths.yaml
    quit







Usage:
    shelephant_hostinfo [options] <host.yaml>

Options:
    -p, --path=N    Path where files are stored in the YAML-file, separated by "/". [default: /files]
        --dir=N     Path where prefix-directory is stored in the YAML-file, separated by "/". [default: /working_diectory]
        --prefix=N  Prefix directory.
        --hash=N    Checksum generated on the host.
        --host=N    Hostname.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/shelephant
'''

def main():

    pass

if __name__ == '__main__':

    main()
