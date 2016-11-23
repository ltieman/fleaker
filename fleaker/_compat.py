# ~*~ coding: utf-8 ~*~
"""
fleaker._compat
~~~~~~~~~~~~~~~

A small series of compatibility functions and wrappers for internal use, so we
aren't tied to any particular compat library.
"""

import sys

PY2 = sys.version_info.major == 2

if PY2:
    text_type = unicode
    string_types = (str, unicode)
else:
    text_type = str
    string_types = (str,)
