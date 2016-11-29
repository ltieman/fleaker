# -*- coding: utf-8 -*-
"""Constants that can be used inside and outside of Fleaker.

Attributes:
    DEFAULT_DICT (werkzeug.datastructures.ImmutableDict): This value can be
        safely used as a default argument for any functions that take
        a ``dict`` for that value. The upside to using this instead of ``None``
        is that you can directly use dictionary specific methods without
        checking the type first.
    MISSING (fleaker.missing.MissingSentinel): This is a sentinel value that
        can be used when ``None`` is a valid value for the variable.
"""

from werkzeug.datastructures import ImmutableDict

from .missing import MissingSentinel


DEFAULT_DICT = ImmutableDict()
MISSING = MissingSentinel()
