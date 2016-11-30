# ~*~ coding: utf-8 ~*~
"""
tests.orm.test_peewee
~~~~~~~~~~~~~~~~~~~~~

Tests for the PeeWee ORM implementation.

Only run if PeeWee is installed.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import pytest

import fleaker

from fleaker.constants import MISSING

peewee = pytest.importorskip('peewee')
flask_utils = pytest.importorskip('playhouse.flask_utils')

SQLITE_DB_CONFIG = 'sqlite://test_db.db'


def _create_app(backend='peewee'):
    """Helper function to make an app for this test module."""
    app = fleaker.App.create_app('tests.orm', orm_backend=backend)
    app.config['DATABASE'] = SQLITE_DB_CONFIG

    return app


def test_orm_peewee_basic_setup():
    """Ensure that our App is automatically and properly setup."""
    app = _create_app()

    assert app.extensions['peewee']
    assert isinstance(fleaker.db, flask_utils.FlaskDB)
    assert not hasattr(fleaker.db, 'session')  # ensure it's not SQLA

    # now do a query and make sure we point to the right sqlite instance/db;
    # also test `get_object_or_404` to ensure it's the proper overridden
    # FlaskDB that PeeWee is providing


def test_orm_peewee_basic_mysql():
    """Ensure an ORM can be properly configured against MySQL."""
    app = _create_app()
    app.config['DATABASE'] = 'mysql://root:badpw@0.0.0.0.0:3306/dne'

    with pytest.raises(RuntimeError):
        # now query and ensure this fails
        pass
    # test should fail; but we should be able to assert that we can connect to
    # MySQL


def test_orm_peewee_basic_model():
    """Ensure we can extend our DB class and implement new models."""
    app = _create_app()

    class TestModel(fleaker.db.Model):
        name = peewee.CharField()

    name = 'Tester'
    tester = TestModel(name=name)
    tester.save()

    assert tester.id
    assert tester.name == name
    # create a new model extended off the proper property and ensure we can hit
    # sqlite
    # @TODO: Make sure we cleanup sqlite db's!


def test_orm_peewee_per_request_connections():
    """Ensure we're making a new connection for each request."""
    # ensure that connection is falsey when we first create this; then enter an
    # app context and ensure is non-falsey; then leave and ensure it's falsey
    # again
    app = _create_app()

    assert app.extensions['peewee']
    assert isinstance(fleaker.db, flask_utils.FlaskDB)

    assert not fleaker.db.connection

    with app.app_context():
        assert fleaker.db.connection
        assert fleaker.db.connection.url == SQLITE_DB_CONFIG
