"""Module that provides a custom test client for Flask testing.

This modules extends ``flask_testing.FlaskClient`` and the only thing it adds
is the ability to easily send JSON to a route during testing, through the
``json`` kwarg to any testing method that sends HTTP requests. This matches the
behavior of ``requests``, which is the best library ever.

It is recommended that you use ``pytest-flask_`` for testing your applications,
as it will make some of this easier.

Example:
    This module automatically registers itself duing application
    initialization. All you need to do is have your app factory use
    ``fleaker.App`` and this will just work.

    .. code-block:: python

        import pytest

        from fleaker import App

        # This is your application's app factory. It must extend off of
        # fleaker.App for this to work transparently.
        def create_app():
            return App()

        # Create your app fixture
        @pytest.fixture
        def app():
            app = create_app()
            return app

        # This is a test that will send a JSON request to a route. The client
        # fixture that is passed in is the one defined in this module.
        def test_login(client):
            data = {
                'email': 'bob@example.com',
                'password': 'correct horse battery staple'
            }
            # No need to dump the JSON and set the content type, we gotchu.
            resp = client.post('/login', json=data)

            assert resp == 200


.. _pytest-flask: https://pypi.python.org/pypi/pytest-flask
"""

from flask import Response as BaseResponse, json
from flask.testing import FlaskClient as BuiltinClient
from werkzeug.utils import cached_property

from .base import BaseApplication


class Response(BaseResponse):
    """An overloaded ``flask.Response`` class that will be used in tests."""

    @cached_property
    def json(self):
        return json.loads(self.data)


class FlaskClient(BuiltinClient):
    """An overloaded ``flask.testing.FlaskClient`` that supports sending JSON
    transparently to routes during testing.
    """

    def open(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['data'] = json.dumps(kwargs.pop('json'))
            kwargs['content_type'] = 'application/json'

        return super(FlaskClient, self).open(*args, **kwargs)


class FlaskClientAwareApp(BaseApplication):

    def __init__(self, *args, **kwargs):
        super(FlaskClientAwareApp, self).__init__(*args, **kwargs)

        self.test_client_class = FlaskClient
        self.response_class = Response
