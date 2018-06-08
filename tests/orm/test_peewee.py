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
import fleaker.orm

from fleaker.constants import MISSING

from tests._compat import mock
from tests.orm.conftest import SQLITE_DATABASE_NAME

peewee = pytest.importorskip('peewee')
flask_utils = pytest.importorskip('playhouse.flask_utils')

SQLITE_DB_CONFIG = 'sqlite:///{}'.format(SQLITE_DATABASE_NAME)


def _create_app(backend='peewee'):
    """Helper function to make an app for this test module."""
    app = fleaker.App.create_app('tests.orm', orm_backend=backend)

    return app


def _create_model_class(class_=None):
    """Helper function to create a model class for testing, so we can ensure it
    gets redefined every time.

    The model we create will have two fields: name and id. Name is a VARCHAR of
    max length 32.

    Args:
        class_ (type|None): The Base class for the model. Uses
            ``fleaker.db.Model`` if nothing is provided.

    Returns:
        type: Returns the newly created BasicModel.
    """
    if class_ is None:
        class_ = fleaker.db.Model

    class BasicModel(class_):
        name = peewee.CharField(max_length=32)
    return BasicModel


@pytest.fixture(autouse=True)
def _close_db():
    """Ensure we close the DB after every test."""
    yield

    if not fleaker.db.database.is_closed():
        fleaker.db.database.close()


@mock.patch.object(fleaker.orm.ORMAwareApp, '_init_peewee_ext',
                   wraps=fleaker.orm.ORMAwareApp._init_peewee_ext)
def test_orm_peewee_basic_setup(mock_init_peewee_ext, sqlite_db):
    """Ensure that our App is automatically and properly setup."""
    app = _create_app()

    # shouldn't be called yet because we aren't configured
    assert mock_init_peewee_ext.call_count == 0

    app.configure({
        'DATABASE': SQLITE_DB_CONFIG,
    })

    # now that we're configured it should be called
    assert mock_init_peewee_ext.call_count == 1

    # PeeWee isn't a great Flask citizen, so it will set this as the app no
    # matter what =/
    assert fleaker.db._app is app

    assert isinstance(fleaker.db._get_current_object(), flask_utils.FlaskDB)
    assert isinstance(fleaker.db.database.obj, peewee.SqliteDatabase)
    assert not hasattr(fleaker.db, 'session')  # ensure it's not SQLA

    model = _create_model_class()

    name = 'Bruce'
    inst = model(name=name)
    inst.save()

    query = model.select().where(model.name == name)

    assert query.get() == inst
    assert flask_utils.get_object_or_404(model, query) == inst


@mock.patch.object(fleaker.orm.ORMAwareApp, '_init_peewee_ext',
                   wraps=fleaker.orm.ORMAwareApp._init_peewee_ext)
def test_orm_peewee_init_reschedules(mock_init_peewee_ext):
    """Ensure that calling configure without a DATABASE param reschedules
    initing peewee.
    """
    app = _create_app()

    # not called yet
    assert mock_init_peewee_ext.call_count == 0

    app.configure({
        'FOO': 'bar',
    })

    # called once, but should be scheduled again
    assert mock_init_peewee_ext.call_count == 1

    assert fleaker.db._app is not app
    # @TODO (tests): Make this test the actual connection string;
    # unfortunately due to how the module is implemented resetting the entire
    # state for the PeeWee extension is INCREDIBLY difficult and I simply don't
    # have time =/; in the meantime, right now this value is likely set to
    # None or the last app used, so it works
    # assert fleaker.db.database.database != SQLITE_DATABASE_NAME
    # assert not isinstance(fleaker.db._get_current_object(), flask_utils.FlaskDB)
    # assert not isinstance(fleaker.db.database, peewee.SqliteDatabase)

    app.configure({
        'DATABASE': SQLITE_DB_CONFIG,
    })

    # NOW it's called and finished
    assert mock_init_peewee_ext.call_count == 2

    assert fleaker.db._app is app
    assert fleaker.db.database.database == SQLITE_DATABASE_NAME
    assert isinstance(fleaker.db._get_current_object(), flask_utils.FlaskDB)
    assert isinstance(fleaker.db.database.obj, peewee.SqliteDatabase)

    # make sure it's not called AGAIN
    app.configure({
        'BAR': 'baz',
    })

    assert mock_init_peewee_ext.call_count == 2


def test_orm_peewee_basic_mysql():
    """Ensure an ORM can be properly configured against MySQL."""
    app = _create_app()

    # this won't work, but it will fail due to missing drivers and that's all
    # we care about
    app.configure({'DATABASE': 'mysql://root:badpw@0.0.0.0.0:3306/dne'})
    err_msg = "MySQLdb or PyMySQL must be installed"

    # this sucker is lazy, so force it
    with pytest.raises(peewee.ImproperlyConfigured, message=err_msg):
        fleaker.db.database.connect()


@pytest.mark.parametrize("model_class", [
    None,
    fleaker.orm.PeeweeModel,
])
def test_orm_peewee_basic_model(model_class, sqlite_db):
    """Ensure we can extend our DB class and implement new models."""
    app = _create_app()
    app.configure({
        'DATABASE': SQLITE_DB_CONFIG,
    })

    model = _create_model_class(class_=model_class)

    with app.app_context():
        name = 'Bruce'
        tester = model(name=name)
        tester.save()

    assert tester.id
    assert tester.name == name

    with app.app_context():
        inst = model.select().where(model.name ==  name).get()
        assert inst == tester

    # create a new model extended off the proper property and ensure we can hit
    # sqlite
    # @TODO: Make sure we cleanup sqlite db's!


def test_orm_peewee_per_request_connections():
    """Ensure we're making a new connection for each request."""
    # ensure that connection is falsey when we first create this; then enter an
    # app context and ensure is non-falsey; then leave and ensure it's falsey
    # again
    app = _create_app()

    app.configure({"DATABASE": SQLITE_DB_CONFIG})

    assert fleaker.db._app is app
    assert isinstance(fleaker.db._get_current_object(), flask_utils.FlaskDB)
    assert isinstance(fleaker.db.database.obj, peewee.SqliteDatabase)

    assert not fleaker.db.database._state.conn

    with app.test_client() as client:
        rv = client.get('/')
        assert fleaker.db.database._state.conn


def test_orm_peewee_creation_with_explicit_db():
    """Ensure we can create the PeeWee Ext by providing a DB URI ourselves.

    Some apps won't be ``MultiStageConfigurable``, so we'll need something like
    this."""
    app = fleaker.orm.ORMAwareApp.create_app('tests.orm',
                                             peewee_database=SQLITE_DB_CONFIG)

    assert app.config['DATABASE'] == SQLITE_DB_CONFIG
    assert fleaker.db._app is app
    assert isinstance(fleaker.db._get_current_object(), flask_utils.FlaskDB)
    assert isinstance(fleaker.db.database.obj, peewee.SqliteDatabase)

    # @TODO (tests): should likely query in here
