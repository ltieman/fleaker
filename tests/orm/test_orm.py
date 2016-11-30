# ~*~ coding: utf-8 ~*~
"""
tests.orm.test_orm
~~~~~~~~~~~~~~~~~~~~~

Tests for the generic ORM implementation. This will always run and tests some
light things such as properly throwing configuration errors.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import pytest

import fleaker

from fleaker.constants import MISSING
from fleaker.orm import _PEEWEE_BACKEND, _SQLALCHEMY_BACKEND


def _create_app(backend=None):
    """Helper function to make an app for this test module."""
    return fleaker.App.create_app('tests.orm', orm_backend=backend)


def _require_both_orms():
    """Run a pytest.skip if either peewee or SQLAlchemy are not installed."""
    sqlalchemy = pytest.importorskip("sqlalchemy")
    peewee = pytest.importorskip('peewee')
    flask_utils = pytest.importorskip('playhouse.flask_utils')

    return (sqlalchemy, peewee, flask_utils)


def test_orm_bad_backend():
    """Ensure a bad backend produces the proper error."""
    backend = 'foo'
    err_msg = ("Explicit ORM backend provided, but could not recognize the "
               "value! Valid values are: '{}'  and '{}'; received: '{}' "
               "instead!")
    err_msg = err_msg.format(_PEEWEE_BACKEND, _SQLALCHEMY_BACKEND, backend)
    with pytest.raises(RuntimeError, message=err_msg):
        _create_app(backend=backend)


def test_orm_both_installed():
    """Ensure that if SQLA and PeeWee are both installed we can specify."""
    _require_both_orms()

    app = _create_app(backend='peewee')

    # some sort of magic to tell the app to use peewee... maybe an arg above?

    assert app.extensions['peewee']
    assert isinstance(fleaker.db, flask_utils.FlaskDB)

    # should be some sort of config value or something to determine which of
    # the two we can use, JUST IN CASE you need both ORM's installed side by
    # side

    # @TODO: now repeat with SQLA


def test_orm_both_installed_error():
    """Ensure that if both ORMs are installed and we don't specify, we error
    out.
    """
    _require_both_orms()

    err_msg = ('Both PeeWee and SQLAlchemy detected as installed, but no '
               'explicit backend provided! Please specify one!')
    with pytest.raises(RuntimeError, message=err_msg):
        app = _create_app(backend=MISSING)


def test_orm_swap_backends_error():
    """Ensure you cannot swap backends on the fly.

    This is in place because we simply don't support that right now, but
    there's minimal reason we can't in the long run.
    """
    _require_both_orms()

    app = _create_app(backend='peewee')

    with pytest.raises(RuntimeError):
        app = _create_app(backend='sqlalchemy')

    # reset the backend
    setattr(fleaker.orm, '_SELECTED_BACKEND', MISSING)

    app = _create_app(backend='sqlalchemy')

    with pytest.raises(RuntimeError):
        app = _create_app(backend='peewee')
