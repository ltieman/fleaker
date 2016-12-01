# ~*~ coding: utf-8 ~*~
"""
tests._compat
~~~~~~~~~~~~~

Compatibility functions for writing tests that work in Python 3 and Python 2.

For the most part, mostly handles mock.

@TODO (tests): I think if we convert to pytest-mock, we can drop this!
"""

from fleaker._compat import PY2


if PY2:
    import mock
else:
    from unittest import mock
