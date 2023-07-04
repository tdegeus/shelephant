
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

    shelephant.ssh.is_file
    shelephant.ssh.is_dir
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

    shelephant.compute_hash.compute_sha256

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

    shelephant.cli.shelephant_cp
    shelephant.cli.shelephant_diff
    shelephant.cli.shelephant_dump
    shelephant.cli.shelephant_hostinfo
    shelephant.cli.shelephant_mv
    shelephant.cli.shelephant_parse
    shelephant.cli.shelephant_rm

Details
-------

.. automodule:: shelephant
    :members:

cli
:::

.. automodule:: shelephant.cli
    :members:

compute_hash
::::::::::::

.. automodule:: shelephant.compute_hash
    :members:

convert
:::::::

.. automodule:: shelephant.convert
    :members:

dataset
:::::::

.. autoclass:: shelephant.dataset.Location
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
