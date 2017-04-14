"""Fixtures for Peewee related unit tests."""

import os
import uuid

import pytest

from flask_login import LoginManager

from fleaker import App, db
from tests.constants import SQLITE_DATABASE_NAME


login_manager = LoginManager()


@pytest.fixture(scope='function')
def peewee_app():
    """Pytest fixture that configures the app to use Peewee."""
    try:
        os.remove(SQLITE_DATABASE_NAME)
    except Exception:
        pass

    app = App.create_app(__name__, orm_backend='peewee')
    app.configure({
        'DATABASE': 'sqlite:///' + 'test_db.db',
        'SECRET_KEY': uuid.uuid4().hex,
    })

    login_manager.init_app(app)

    with app.app_context(), app.test_request_context():
        yield app


@pytest.fixture
def database(peewee_app):
    """Fixture that provides a temporary database for testing."""
    yield db

    try:
        os.remove(SQLITE_DATABASE_NAME)
    except Exception:
        pass
