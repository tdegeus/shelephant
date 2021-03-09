r'''
Yaml IO.

(c) Tom de Geus, 2021, MIT
'''

import yaml
import click
import os

from . import convert


def read(filename):
    r'''
Read YAML file and return its content.
    '''

    if not os.path.isfile(filename):
        raise IOError('"{0:s} does not exist'.format(filename))

    with open(filename, 'r') as file:
        return yaml.load(file.read(), Loader=yaml.FullLoader)


def read_item(filename, key=[]):
    r'''
Get an item from a YAML file.

:type key: str or list
:param key:
    The item to read. E.g.
    *   ``[]`` for a YAML file containing only a list.
    *   ``['foo']`` for a plain YAML file.
    *   ``['key', 'to', foo']`` for a YAML file with nested items.

    An item specified as ``str`` separated by "/" is also accepted.

:return:
    The read item.
    '''

    data = read(filename)

    if type(data) == dict:
        return convert.get(data, key)

    key = convert.split_key(key)

    if type(data) == list and len(key) == 0:
        return data

    raise IOError('"{0:s}" not in "{1:s}"'.format('/'.join(key), filename))


def dump(filename, data, force=False):
    r'''
Dump data to YAML file.

:type filename: str
:param filename: The output filename.

:type data: list, dict
:param data: The data to dump.

:type force: bool, optional
:param force: Do not prompt to overwrite file.
    '''

    dirname = os.path.dirname(filename)

    if not force:
        if os.path.isfile(filename):
            if not click.confirm('Overwrite "{0:s}"?'.format(filename)):
                raise IOError('Cancelled')
        elif not os.path.isdir(dirname) and len(dirname) > 0:
            if not click.confirm('Create "{0:s}"?'.format(os.path.dirname(filename))):
                raise IOError('Cancelled')

    if not os.path.isdir(dirname) and len(dirname) > 0:
        os.makedirs(os.path.dirname(filename))

    with open(filename, 'w') as file:
        ret = yaml.dump(data, file)


def view(data):
    r'''
Print data formatted as YAML.
    '''
    print(yaml.dump(data, default_flow_style=False, default_style=''))

