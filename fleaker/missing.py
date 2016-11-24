# ~*~ coding: utf-8 ~*~
"""
fleaker.missing
~~~~~~~~~~~~~~~

This module defines a reliable sentinel value that can be used as a default
value, especially when ``None``, ``True``, and ``False`` can be a valid values
for the function.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""


# @TODO Make this work as an empty iterator?
class MissingSentinel(object):
    """This class can be used to create an object that can be used as
    a flexible sentinel value. These can be very useful for default keyword
    arguments that can be boolean values and you want to test `None`. They can
    also be used like a boolean in an `if` statement, as this object will
    always evaluate to `False` when cast to a boolean.

    >> MISSING = MissingSentinel()
    >> bool(MISSING) is False
    True
    >> False is not MISSING
    True
    >> print("success") if not MISSING else print("failure")
    "success"

    .. versionadded:: 0.1.1
    """
    def __bool__(self):
        """Define the boolean value for this object.

        This method in Python 3.x is used in boolean expressions to determine
        the truthy value of the variable. Since this class represents that
        something is missing, it stands to reason that it should evaluate to
        ``False``. It is aliased to ``__nonzero__`` for Python 2.
        """
        return False

    def __len__(self):
        """Define the length of this instance, which will always be 0."""
        return 0

    # Python 2 aliases
    __nonzero__ = __bool__
