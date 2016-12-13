# ~*~ coding: utf-8 ~*~
"""
fleaker.utils
~~~~~~~~~~~~~~~~~

The Fleaker utils module provides a number of small helper functions to make
working with Flask and Fleaker easier. It is mostly intended for internal use,
but it is technically a public API, so treat it as such!

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from flask import current_app


def in_app_context(app=None):
    """Are we currently in an application context?

    Kwargs:
        app (werkzeug.local.LocalProxy): An optional proxy you can pass to this
            method for checking. If this is not passed, we will check
            ``current_app``, however sometimes you want to pass an explicit
            proxy for checking.
    """
    if app is None:
        app = current_app

    # This is the best way to check if current_app is a proxy.
    return bool(dir(app))
