r'''
Convert nested ``list`` or ``dict``.

(c) Tom de Geus, 2021, MIT
'''

from collections import defaultdict
import collections.abc

def _flatten_detail(data):
    r'''
Detail of :py:fun:`Flatten`.
Not part of public API.

See https://stackoverflow.com/a/17485785/2646505
    '''

    for item in data:
        if isinstance(item, collections.abc.Iterable) and not isinstance(item, str):
            for x in flatten(item):
                yield x
        else:
            yield item


def flatten(data):
    r'''
Flatten a nested list to a one dimensional list.
    '''
    return list(_flatten_detail(data))


def _squash_detail(data, parent_key='', sep='_'):
    r'''
Detail of :py:fun:`squash`.
Not part of public API.

See https://stackoverflow.com/a/6027615/2646505
    '''

    items = []

    for k, v in data.items():

        new_key = parent_key + sep + k if parent_key else k

        if isinstance(v, collections.abc.MutableMapping):
            items.extend(_squash_detail(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def squash(data):
    r'''
Squash a dictionary to a single list.
    '''

    return flatten(list(_squash_detail(data).values()))


