# -*- coding: utf-8 -*-
"""Constants that can be used inside and outside of Fleaker.

Attributes:
    DEFAULT_DICT (fleaker.missing.MissingDictSentinel): This value can be
        safely used as a default argument for any functions that take
        a ``dict`` for that value. The upside to using this instead of ``None``
        is that you can directly use dictionary specific methods without
        checking the type first, and the dictionary is immutable so you can
        safely use it like you would expect!
    MISSING (fleaker.missing.MissingSentinel): This is a sentinel value that
        can be used when ``None`` is a valid value for the variable.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from .missing import MissingDictSentinel, MissingSentinel


DEFAULT_DICT = MissingDictSentinel()
MISSING = MissingSentinel()
