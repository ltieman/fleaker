# ~*~ coding: utf-8 ~*~
"""
fleaker._compat
~~~~~~~~~~~~~~~

A small series of compatibility functions and wrappers for internal use, so we
aren't tied to any particular compat library.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sys

PY2 = sys.version_info.major == 2

if PY2:
    text_type = unicode
    string_types = (str, unicode)
    from urllib import urlencode
    iteritems = lambda dictlike: dictlike.iteritems()

    # taken straight from werkzeug:
    # https://github.com/pallets/werkzeug/blob/0bc61df6e1ae9f2ffdf5d066aa3cd9d5ebcb307d/werkzeug/_compat.py#L105
    def to_bytes(x, charset=sys.getdefaultencoding(), errors='strict'):
        """Convert an object to bytes."""
        if x is None:
            return None
        if isinstance(x, (bytes, bytearray, buffer)):
            return bytes(x)
        if isinstance(x, unicode):
            return x.encode(charset, errors)
        raise TypeError('Expected bytes')

    def exception_message(exc):
        """Helper function to access an Exception's message."""
        return exc.message

else:
    text_type = str
    string_types = (str,)
    from urllib.parse import urlencode
    iteritems = lambda dictlike: iter(dictlike.items())

    # taken straight from werkzeug:
    # https://github.com/pallets/werkzeug/blob/0bc61df6e1ae9f2ffdf5d066aa3cd9d5ebcb307d/werkzeug/_compat.py#L183
    def to_bytes(x, charset=sys.getdefaultencoding(), errors='strict'):
        """Convert an object to bytes."""
        if x is None:
            return None
        if isinstance(x, (bytes, bytearray, memoryview)):  # noqa
            return bytes(x)
        if isinstance(x, str):
            return x.encode(charset, errors)
        raise TypeError('Expected bytes')

    def exception_message(exc):
        """Helper function to access and Exception's message."""
        return exc.args[0]
