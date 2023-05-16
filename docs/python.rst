
*************
Python module
*************

Dataset
-------

.. autosummary::

    shelephant.dataset.Location

SSH interface
-------------

.. autosummary::

    shelephant.ssh.file_exists
    shelephant.ssh.has_keys_set
    shelephant.ssh.tempdir

scp interface
-------------

.. autosummary::

    shelephant.scp.copy

rsync interface
---------------

.. autosummary::

    shelephant.rsync.diff
    shelephant.rsync.copy

local interface
---------------

.. autosummary::

    shelephant.local.diff
    shelephant.local.copy
    shelephant.local.remove
    shelephant.local.move

Type conversion
---------------

.. autosummary::

    shelephant.convert.flatten
    shelephant.convert.squash
    shelephant.convert.get
    shelephant.convert.split_key

YAML handling
-------------

.. autosummary::

    shelephant.yaml.read
    shelephant.yaml.read_item
    shelephant.yaml.dump
    shelephant.yaml.preview

File information
----------------

.. autosummary::

    shelephant.info.getinfo

File operations
---------------

.. autosummary::

    shelephant.path.filter_deepest
    shelephant.path.dirnames
    shelephant.path.makedirs

Formatted print
---------------

.. autosummary::

    shelephant.output.copyplan

Command-line interface
----------------------

.. autosummary::

    shelephant.shelephant_cp
    shelephant.shelephant_diff
    shelephant.shelephant_dump
    shelephant.shelephant_hostinfo
    shelephant.shelephant_mv
    shelephant.shelephant_parse
    shelephant.shelephant_rm

Details
-------

.. automodule:: shelephant
    :members:

convert
:::::::

.. automodule:: shelephant.convert
    :members:

dataset
:::::::

.. autoclass:: shelephant.dataset.Location
    :members:

info
::::

.. automodule:: shelephant.info
    :members:

local
:::::

.. automodule:: shelephant.local
    :members:

output
::::::

.. automodule:: shelephant.output
    :members:

path
::::

.. automodule:: shelephant.path
    :members:

rsync
:::::

.. automodule:: shelephant.rsync
    :members:

scp
:::

.. automodule:: shelephant.scp
    :members:

search
::::::

.. automodule:: shelephant.search
    :members:

ssh
:::

.. automodule:: shelephant.ssh
    :members:

yaml
::::

.. automodule:: shelephant.yaml
    :members:
