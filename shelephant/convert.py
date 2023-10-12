import collections.abc
import functools
import operator


def _flatten_detail(data):
    r"""
    Detail of :py:fun:`Flatten`.
    See https://stackoverflow.com/a/17485785/2646505
    """

    for item in data:
        if isinstance(item, collections.abc.Iterable) and not isinstance(item, str):
            yield from flatten(item)
        else:
            yield item


def flatten(data: list[list]) -> list:
    """
    Flatten a nested list to a one dimensional list.

    :param data: A nested list.
    :return: A one dimensional list.
    """
    return list(_flatten_detail(data))


def _squash_detail(data, parent_key="", sep="_"):
    r"""
    Detail of :py:fun:`squash`.
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


def squash(data: dict[list]) -> list:
    """
    Squash a dictionary to a single list.
    For example::

        >>> squash({"foo": [1, 2], "bar": {"foo": [3, 4], "bar": 5}})
        [1, 2, 3, 4, 5]

    :param data: A nested dictionary.
    :return: A one dimensional list.
    """

    return flatten(list(_squash_detail(data).values()))


def split_key(key: str) -> list[str]:
    """
    Split a key separated by "/" in a list.

    :param key: A key.
    :return: A list of key components.
    """

    if isinstance(key, list):
        return key

    if isinstance(key, str):
        return key.split("/")

    raise OSError(f"'{key}' cannot be split")


def get(data: dict[dict], key: str | list[str]) -> dict | list | str | int | float:
    r"""
    Get an item from a nested dictionary.

    :param data: A nested dictionary.
    :param key:
        The item to read. E.g.
        *   ``[]`` for a YAML file containing only a list.
        *   ``['foo']`` for a plain YAML file.
        *   ``['key', 'to', foo']`` for a YAML file with nested items.

        An item specified as ``str`` separated by "/" is also accepted.

    :return:
        The read item.
    """

    assert isinstance(data, dict)
    key = split_key(key)

    if len(key) > 0:
        try:
            return functools.reduce(operator.getitem, key, data)
        except KeyError:
            raise OSError('"{:s}" not found'.format("/".join(key)))

    return data
