r"""
Yaml IO.

(c) Tom de Geus, 2021, MIT
"""
import os

import click
import yaml

from . import convert


def read(filename):
    r"""
    Read YAML file and return its content.
    """

    if not os.path.isfile(filename):
        raise OSError(f'"{filename:s} does not exist')

    with open(filename) as file:
        return yaml.load(file.read(), Loader=yaml.FullLoader)


def read_item(filename, key=[]):
    r"""
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
    """

    data = read(filename)

    if type(data) == dict:
        return convert.get(data, key)

    key = convert.split_key(key)

    if type(data) == list and len(key) == 0:
        return data

    raise OSError('"{:s}" not in "{:s}"'.format("/".join(key), filename))


def dump(filename, data, force=False):
    r"""
    Dump data to YAML file.

    :type filename: str
    :param filename: The output filename.

    :type data: list, dict
    :param data: The data to dump.

    :type force: bool, optional
    :param force: Do not prompt to overwrite file.
    """

    dirname = os.path.dirname(filename)

    if not force:
        if os.path.isfile(filename):
            if not click.confirm(f'Overwrite "{filename:s}"?'):
                raise OSError("Cancelled")
        elif not os.path.isdir(dirname) and len(dirname) > 0:
            if not click.confirm(f'Create "{os.path.dirname(filename):s}"?'):
                raise OSError("Cancelled")

    if not os.path.isdir(dirname) and len(dirname) > 0:
        os.makedirs(os.path.dirname(filename))

    with open(filename, "w") as file:
        yaml.dump(data, file)


def view(data):
    r"""
    Print data formatted as YAML.
    """
    print(yaml.dump(data, default_flow_style=False, default_style=""))
