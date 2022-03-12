import os


def chroot(files, old_root, new_root, in_place=False):
    r"""
    Change the root of relative paths.
    Skip if all paths are absolute paths.

    If ``in_place = True`` the input list is modified 'in place' (and a pointer to it is returned),
    otherwise a new list is returned.
    """

    isabs = [os.path.isabs(file) for file in files]

    if any(isabs) and not all(isabs):
        raise OSError("Specify either relative or absolute files-paths")

    if all(isabs):
        return files

    if not in_place:
        return [
            os.path.relpath(os.path.abspath(os.path.join(old_root, file)), new_root)
            for file in files
        ]

    for i in range(len(files)):
        files[i] = os.path.relpath(os.path.abspath(os.path.join(old_root, files[i])), new_root)

    return files


def add_prefix(prefix, files):
    r"""
    Add prefix to a list of filenames.
    Skip if all paths are absolute paths.

    :param str prefix: The prefix.
    :param list files: List of paths.
    :return: List of paths.
    """

    isabs = [os.path.isabs(file) for file in files]

    if any(isabs) and not all(isabs):
        raise OSError("Specify either relative or absolute files-paths")

    if all(isabs):
        return files

    return [os.path.normpath(os.path.join(prefix, file)) for file in files]
