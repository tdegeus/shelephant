r"""
Convert nested ``list`` or ``dict``.

(c) Tom de Geus, 2021, MIT
"""
import collections.abc
import functools
import operator


def _flatten_detail(data):
    r"""
    Detail of :py:fun:`Flatten`.
    Not part of public API.

    See https://stackoverflow.com/a/17485785/2646505
    """

    for item in data:
        if isinstance(item, collections.abc.Iterable) and not isinstance(item, str):
            yield from flatten(item)
        else:
            yield item


def flatten(data):
    r"""
    Flatten a nested list to a one dimensional list.
    """
    return list(_flatten_detail(data))


def _squash_detail(data, parent_key="", sep="_"):
    r"""
    Detail of :py:fun:`squash`.
    Not part of public API.

    See https://stackoverflow.com/a/6027615/2646505
    """

    items = []

    for k, v in data.items():

        new_key = parent_key + sep + k if parent_key else k

        if isinstance(v, collections.abc.MutableMapping):
            items.extend(_squash_detail(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def squash(data):
    r"""
    Squash a dictionary to a single list.
    """

    return flatten(list(_squash_detail(data).values()))


def split_key(key):
    r"""
    Split a key separated by "/" in a list.
    """

    if type(key) == list:
        return key

    if type(key) == str:
        return key.split("/")

    raise OSError(f"'{key}' cannot be split")


def get(data, key):
    r"""
    Get an item from a nested dictionary.

    :param dict data:
        A nested dictionary.

    :type key: str or list
    :param key:
        The item to read. E.g.
        *   ``[]`` for a YAML file containing only a list.
        *   ``['foo']`` for a plain YAML file.
        *   ``['key', 'to', foo']`` for a YAML file with nested items.

        An item specified as ``str`` separated by "/" is also accepted.

    :return:
        The read item.
    """

    assert type(data) == dict
    key = split_key(key)

    if len(key) > 0:
        try:
            return functools.reduce(operator.getitem, key, data)
        except KeyError:
            raise OSError('"{:s}" not found'.format("/".join(key)))

    return data
