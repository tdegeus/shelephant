
import yaml
import functools
import operator
import click
import os


def read(filename):
    r'''
Read YAML file and return its content as ``list`` or ``dict``.
    '''

    if not os.path.isfile(filename):
        raise IOError('"{0:s} does not exist'.format(filename))

    with open(filename, 'r') as file:
        return yaml.load(file.read(), Loader=yaml.FullLoader)


def read_item(filename, key=[]):
    r'''
Get an item from a YAML file.
Optionally the key to the item can be specified as a list. E.g.
*   ``[]`` for a YAML file containing only a list.
*   ``['foo']`` for a plain YAML file.
*   ``['key', 'to', foo']`` for a YAML file with nested items.
    '''

    data = read(filename)

    if len(key) == 0 and type(data) != list:
        raise IOError('Specify key for "{0:s}"'.format(filename))

    if len(key) > 0:
        try:
            return functools.reduce(operator.getitem, key, data)
        except:
            raise IOError('"{0:s}" not in "{1:s}"'.format('/'.join(key), filename))

    return data


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

