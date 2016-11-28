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
else:
    text_type = str
    string_types = (str,)

# Grab the stack based upon what version of Flask we are using
try:
    from flask import _app_ctx_stack as STACK
except ImportError:
    from flask import _request_ctx_stack as STACK
