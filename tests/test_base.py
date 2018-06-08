# ~*~ coding: utf-8 ~*~
"""
tests.test_base
~~~~~~~~~~~~~

Tests for the Fleaker :class:`BaseApplication`.
"""

import flask
import pytest

import fleaker

from fleaker.base import BaseApplication

from tests._compat import mock


def _create_app():
    """Create an app to aid in testing"""
    return BaseApplication.create_app('tests')


def test_base_whitelist_kwargs():
    """Ensure whitelist kwargs works."""
    kwargs = {
        'static_path': 'foo',
        'static_url_path': 'bar',
        'root_path': None,
        'template_folder': 'custom',
        'bad': 'bad',
        'orm_backend': 'peewee',
    }

    new_kwargs = BaseApplication._whitelist_standard_flask_kwargs(kwargs)

    expected_keys = ('static_url_path', 'root_path', 'template_folder',)
    bad_keys = ('static_path', 'bad', 'orm_backend')

    for key in expected_keys:
        assert key in new_kwargs
        assert kwargs[key] == new_kwargs[key]

    for key in bad_keys:
        assert key not in new_kwargs


def test_base_post_create_app():
    """Ensure the default impl of post_create_app returns the app."""
    app = _create_app()

    post_app = BaseApplication.post_create_app(app)

    assert post_app is app


def test_base_pre_create_app():
    """Ensure the defualt impl of pre_create_app returns the settings passed."""
    settings = {
        'foo': 'bar',
        'baz': 'qux',
        'int': 1,
    }

    new_settings = BaseApplication.pre_create_app(**settings)

    assert new_settings == settings


@mock.patch.object(BaseApplication, 'pre_create_app',
                   wraps=BaseApplication.pre_create_app)
@mock.patch.object(BaseApplication, 'post_create_app',
                   wraps=BaseApplication.post_create_app)
def test_base_create_app(mock_post_create, mock_pre_create):
    """Ensure create_app calls hooks and returns a Flask app."""

    app = _create_app()

    assert isinstance(app, flask.Flask)
    assert app.import_name == 'tests'
    assert mock_post_create.call_count == 1
    assert mock_pre_create.call_count == 1


def test_base_add_post_configure_callback():
    """Ensure attempting to add a post configure callback fails."""
    app = _create_app()

    err_msg = ("`post_configure` callbacks are only implemented on the "
               "MultiStageConfigurableApp! Ensure that mixin is present!")
    with pytest.raises(NotImplementedError, message=err_msg):
        app.add_post_configure_callback(lambda cfg, args: None)
