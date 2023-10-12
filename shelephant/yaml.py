import os
import pathlib

import click
import yaml

from . import convert


def read(filename: str | pathlib.Path, default=None) -> list | dict:
    r"""
    Read YAML file and return its content.

    :param filename: The YAML file to read.
    :param default: The default value to return if the file is empty.
    :return: The content of the YAML file.
    """

    if not os.path.isfile(filename):
        raise OSError(f'"{filename} does not exist')

    with open(filename) as file:
        ret = yaml.load(file.read(), Loader=yaml.FullLoader)
        if ret is None:
            return default
        return ret


def read_item(filename: str | pathlib.Path, key: str | list[str] = []) -> list | dict:
    r"""
    Get an item from a YAML file.

    :param key:
        The item to read. E.g.
        *   ``[]`` for a YAML file containing only a list.
        *   ``['foo']`` for a plain YAML file.
        *   ``['key', 'to', foo']`` for a YAML file with nested items.

        An item specified as ``str`` separated by "/" is also accepted.

    :return: The content of the item.
    """

    data = read(filename)

    if isinstance(data, dict):
        return convert.get(data, key)

    key = convert.split_key(key)

    if isinstance(data, list) and len(key) == 0:
        return data

    raise OSError(f'"{"/".join(key)}" not in "{filename}"')


def dump(
    filename: str | pathlib.Path, data: list | dict, force: bool = False, width: int = float("inf")
):
    """
    Dump data to YAML file.

    :param filename: The output filename.
    :param data: The data to dump.
    :param force: Do not prompt to overwrite file.
    :param width: The maximum line-width of the file.
    """

    dirname = os.path.dirname(filename)

    if not force:
        if os.path.isfile(filename):
            if not click.confirm(f'Overwrite "{filename}"?'):
                raise OSError("Cancelled")
        elif not os.path.isdir(dirname) and len(dirname) > 0:
            if not click.confirm(f'Create "{os.path.dirname(filename)}"?'):
                raise OSError("Cancelled")

    if not os.path.isdir(dirname) and len(dirname) > 0:
        os.makedirs(os.path.dirname(filename))

    with open(filename, "w") as file:
        yaml.dump(data, file, width=width)


def overwrite(filename: str | pathlib.Path, data: list | dict):
    """
    Overwrite existing YAML file with data.
    This function only changes the file if the content has indeed changed.

    :param filename: The output filename.
    :param data: The data to dump.
    """

    if not os.path.isfile(filename):
        return dump(filename, data)

    ret = yaml.dump(data, default_flow_style=False, default_style="")
    old = pathlib.Path(filename).read_text()

    if ret == old:
        return

    pathlib.Path(filename).write_text(ret)


def preview(data: list | dict, width: int = float("inf")):
    r"""
    Print data formatted as YAML.

    :param data: The data to dump.
    :param width: The maximum line-width of the file.
    """
    print(yaml.dump(data, default_flow_style=False, default_style="", width=width))
