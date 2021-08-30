def theme(theme=None):
    r"""
    Return dictionary of colors.

    .. code-block:: python

        {
            'new' : '...',
            'overwrite' : '...',
            'skip' : '...',
            'bright' : '...',
        }

    :param str theme: Select color-theme.

    :rtype: dict
    """

    if theme == "dark":
        return {
            "new": "1;32",
            "overwrite": "1;31",
            "skip": "1;30",
            "bright": "1;37",
        }

    return {
        "new": "",
        "overwrite": "",
        "skip": "",
        "bright": "",
    }


class String:
    r"""
    Rich string.

    .. note::

        All options are attributes, that can be modified at all times.

    .. note::

        Available methods:

        *   ``A.format()`` :  Formatted string.
        *   ``str(A)`` : Unformatted string.
        *   ``A.isnumeric()`` : Return if the "data" is numeric.
        *   ``int(A)`` : Dummy integer.
        *   ``float(A)`` : Dummy float.

    :type data: str, None
    :param data: The data.

    :type width: None, int
    :param width: Print width (formatted print only).

    :type color: None, str
    :param color: Print color, e.g. "1;32" for bold green (formatted print only).

    :type align: ``'<'``, ``'>'``
    :param align: Print alignment (formatted print only).

    :type dummy: 0, int, float
    :param dummy: Dummy numerical value.

    :methods:


    """

    def __init__(self, data, width=None, align="<", color=None, dummy=0):

        self.data = data
        self.width = width
        self.color = color
        self.align = align
        self.dummy = dummy

    def format(self):
        r"""
        Return formatted string: align/width/color are applied.
        """

        if self.width and self.color:
            fmt = "\x1b[{color:s}m{{0:{align:s}{width:d}.{width:d}s}}\x1b[0m".format(
                **self.__dict__
            )
        elif self.width:
            fmt = "{{0:{align:s}{width:d}.{width:d}s}}".format(**self.__dict__)
        elif self.color:
            fmt = "\x1b[{color:s}m{{0:{align:s}s}}\x1b[0m".format(**self.__dict__)
        else:
            fmt = "{{0:{align:s}s}}".format(**self.__dict__)

        return fmt.format(str(self))

    def isnumeric(self):
        r"""
        Return if the "data" is numeric : always zero for this class.
        """
        return False

    def __str__(self):
        return str(self.data)

    def __int__(self):
        return int(self.dummy)

    def __float__(self):
        return float(self.dummy)

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return str(self) < str(other)
