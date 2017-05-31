# ~*~ coding: utf-8 ~*~
"""
tests.test_exceptions
~~~~~~~~~~~~~~~~~

Provides tests for the custom Exceptions Fleaker implements.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import json

import pytest

from flask import redirect, request, session, url_for

from fleaker import App, AppException, DEFAULT_DICT, MISSING, exceptions
from fleaker._compat import to_bytes, urlencode
from fleaker.exceptions import ErrorAwareApp

from tests._compat import mock

SERVER_NAME = 'localhost'
# standard response Flask returns if you raise an uncaught exception
STANDARD_FLASK_500 = to_bytes("""\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>500 Internal Server Error</title>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your \
request.  Either the server is overloaded or there is an error in the \
application.</p>
""")


def _create_app(register_error_handlers=True):
    """Create a small app for help in testing."""
    app = App(__name__)
    app.config['SECRET_KEY'] = 'ITSASECRET'
    app.config['SERVER_NAME'] = SERVER_NAME

    # This is needed to make these tests pass. As of v0.4.0, we register
    # a global 500 errorhandler so that it can be logged. These tests were
    # written by a nut job :)
    app.error_handlers = {}

    @app.route('/app_exc')
    def app_exception():
        """Raise an AppException with some custom parameters."""
        request_args = request.args.to_dict()
        args = request_args.pop('redirect_args', '{}')
        args = json.loads(args)
        raise exceptions.AppException("Testing App exception",
                                      redirect_args=args, **request_args)

    @app.route('/fleaker_exc')
    def fleaker_exception():
        """Raise a FleakerException with some custom parameters."""
        request_args = request.args.to_dict()
        args = request_args.pop('redirect_args', '{}')
        args = json.loads(args)
        raise exceptions.FleakerException("Testing Fleaker exception",
                                          redirect_args=args, **request_args)

    @app.route('/base_exc')
    def base_exception():
        """Raise a FleakerBaseException with some custom parameters."""
        request_args = request.args.to_dict()
        args = request_args.pop('redirect_args', '{}')
        args = json.loads(args)
        raise exceptions.FleakerBaseException("Testing base exception",
                                               redirect_args=args, **request_args)

    @app.route('/redirected')
    def redir_method():
        """Small method to redirect to."""
        return 'OK', 200

    if register_error_handlers:
        # this is more old-Flask friendly than using ``add_errorhandler``.
        app.errorhandler(exceptions.AppException)(
            exceptions.AppException.errorhandler_callback)
        app.errorhandler(exceptions.FleakerException)(
            exceptions.FleakerException.errorhandler_callback)
        app.errorhandler(exceptions.FleakerBaseException)(
            exceptions.FleakerBaseException.errorhandler_callback)

    return app


def _redir_url(fragment, query_args=''):
    """Construct a full, external URL from a fragment using the SERVER_NAME in
    this file.

    Args:
        fragment (str): The query string fragment to turn into a full URL,
            e.g., ``/foo``.
    """
    if fragment.startswith('/'):
        fragment = fragment[1:]

    if query_args:
        # @TODO (test): Ewwww.... fix this
        query_args = json.loads(query_args)
        query_args = '?' + urlencode(query_args)

    return "http://{}/{}{}".format(SERVER_NAME, fragment, query_args)


# please list all custom exceptions here for a quick test
@pytest.mark.parametrize('spec', [
    (exceptions.FleakerBaseException, 'Base Exc', 401),
    (exceptions.FleakerException, 'Fleaker Exc', 402),
    (exceptions.AppException, 'App Exc', 403),
])
def test_exceptions_basic_args(spec):
    """Ensure we can raise Exceptions with a status code and message, or no
    args.
    """
    exc_type, msg, code = spec

    # message and status code should work
    with pytest.raises(exc_type) as exc:
        raise exc_type(msg, status_code=code)

    assert type(exc.value) is exc_type
    assert exc.value.message == msg
    assert exc.value.status_code == code

    # and no args should also work
    with pytest.raises(exc_type) as exc:
        raise exc_type()

    assert type(exc.value) is exc_type
    assert exc.value.message == ''
    assert exc.value.status_code is None
    assert exc.value.redirect is MISSING
    assert exc.value.redirect_args is DEFAULT_DICT
    assert exc.value.prevent_rollback is False
    assert exc.value.flash_message is False
    assert exc.value.flash_level == 'danger'


# @TODO (test): Combine with the flash instantiation test
@pytest.mark.parametrize('spec', [
    (exceptions.FleakerBaseException, '/foo', {'bar': 1},),
    (exceptions.FleakerException, '/bar', {'baz': 1},),
    (exceptions.AppException, '/baz', {'qux': 1},),
])
def test_exception_create_with_redirect(spec):
    """Ensure we can create an exception setup to redirect."""
    exc_type, redirect, redirect_args = spec

    with pytest.raises(exc_type) as exc:
        raise exc_type(redirect=redirect, redirect_args=redirect_args)

    assert exc.value.redirect == redirect
    assert exc.value.redirect_args == redirect_args


@pytest.mark.parametrize('spec', [
    (exceptions.FleakerBaseException, '/base_exc',),
    (exceptions.FleakerException, '/fleaker_exc',),
    (exceptions.AppException, '/app_exc',),
])
def test_exception_handler_auto_redirect(spec):
    """Ensure that handled exceptions properly redirect."""
    app = _create_app()

    exc_type, route = spec

    with app.test_client() as client:
        redirect_args = json.dumps({"test": "redirarg"})
        query_args = {
            'redirect': 'redir_method',
            'redirect_args': redirect_args
        }
        resp = client.get(route, query_string=query_args)
        assert resp.status_code == 302
        assert resp.location == _redir_url('/redirected',
                                           query_args=redirect_args)
        assert "test=redirarg" in resp.location

        # now let's try with a properly defined named route to test url_for
        assert resp.status_code == 302


@pytest.mark.parametrize('spec', [
    (exceptions.FleakerBaseException, 'Joy!', 'success',),
    (exceptions.FleakerException, 'Sorrow!', 'danger',),
    (exceptions.AppException, 'Mixed feelings!', 'warning',),
])
def test_exception_create_with_flash(spec):
    """Ensure we can create a custom exception with flash info."""
    exc_type, msg, level = spec

    stock_message = "foo"

    with pytest.raises(exc_type) as exc:
        raise exc_type(stock_message, flash_message=msg, flash_level=level)

    assert exc.value.message == stock_message
    assert exc.value.flash_message == msg
    assert exc.value.flash_level == level


@pytest.mark.parametrize('spec', [
    (exceptions.FleakerBaseException, '/base_exc', 'Joy!', 'success',),
    (exceptions.FleakerException, '/fleaker_exc', 'Sorrow!', 'danger',),
    (exceptions.AppException, '/app_exc', 'Mixed feelings!', 'warning',),
])
def test_exception_handler_auto_flash(spec):
    """Ensure that we automatically flash the environment when needed."""
    app = _create_app()

    exc_type, route, flash_msg, flash_level = spec

    with app.test_client() as client:
        resp = client.get(
            route,
            query_string={
                'flash_message': flash_msg,
                'flash_level': flash_level
            }
        )

        assert '_flashes' in session
        assert session['_flashes'].pop() == (flash_level, flash_msg)


@pytest.mark.parametrize('spec', [
    (exceptions.FleakerBaseException, '/base_exc', 'Joy', 'success',),
    (exceptions.FleakerException, '/fleaker_exc', 'Sorrow', 'danger',),
    (exceptions.AppException, '/app_exc', 'Mixed!', 'warning',),
])
def test_exception_handler_redirect_with_flash(spec):
    """Ensure flashing and redirecting together works fine."""
    app = _create_app()
    exc_type, route, flash_msg, flash_level = spec

    redirect_args = json.dumps({'redir': 'tested'})

    with app.test_client() as client:
        resp = client.get(
            route,
            query_string={
                'redirect': 'redir_method',
                'flash_message': flash_msg,
                'flash_level': flash_level,
                'redirect_args': redirect_args,
            }
        )

        assert resp.status_code == 302
        assert resp.location == _redir_url('/redirected',
                                           query_args=redirect_args)
        assert '_flashes' in session
        assert session['_flashes'].pop() == (flash_level, flash_msg)


@pytest.mark.skip(reason="While the ORM is finished, this needs implementing")
def test_exception_handler_auto_rollback():
    """Ensure we automatically roll back any open transactions."""


@pytest.mark.parametrize('exc_type', [
    exceptions.FleakerBaseException,
    exceptions.FleakerException,
    exceptions.AppException,
])
def test_exception_handler_registration(exc_type):
    """Ensure we can easily register the exception handler."""
    app = _create_app(register_error_handlers=False)
    assert not app.error_handlers.keys()

    exc_type.register_errorhandler(app)
    assert app.error_handlers[None][exc_type] == exc_type.errorhandler_callback


def test_exception_handler_overridden():
    """Ensure an AppException can be overridden and it's handler still
    works.
    """
    app = _create_app(register_error_handlers=False)
    code = 403
    content = b"My error page."


    class TestException(exceptions.AppException):
        """Simple testing exception."""

        def error_page(self):
            """Return custom error page."""
            return content

    @app.route('/test')
    def throw_error():
        """Throw an error for testing."""
        raise TestException(flash_message='Flashed', status_code=code)

    AppException.register_errorhandler(app)

    with app.test_client() as client:
        resp = client.get('/test')

        assert resp.data == content
        assert resp.status_code == code


def test_exception_handler_chained():
    """Ensure a chain of error handlers with no eror page works fine."""

    app = _create_app(register_error_handlers=False)
    content = b'Success!'

    @app.route('/test')
    def throw_error():
        """Just throw an exc for me."""
        raise AppException('Something suddenly came up!')

    def custom_errorhandler(exc):
        """Return actual content."""
        return content

    AppException.register_errorhandler(app)
    app.errorhandler(AppException)(custom_errorhandler)

    with app.test_client() as client:
        resp = client.get('/test')

        assert resp.data == content


def test_exception_auto_handler_registration():
    """Ensure that the exception mixin automatically registers handlers."""
    app = ErrorAwareApp.create_app('tests')
    app.config['SECRET_KEY'] = 'ITSASECRET'

    # error handlers should be registered by default
    expected_handler = AppException.errorhandler_callback
    assert app.error_handlers[None][AppException] == expected_handler

    msg = 'foo'
    level = 'danger'

    @app.route('/test_exc')
    def test_exc():
        """Throw a simple exception for me."""
        raise AppException(flash_message=msg, flash_level=level)

    with app.test_client() as client:
        res = client.get('/test_exc')

        assert res.data == STANDARD_FLASK_500
        assert '_flashes' in session
        assert session['_flashes'].pop() == (level, msg)


def test_exception_auto_handler_explicit_registration():
    """Ensure that the exception mixin doesn't register handlers when told not
    to.
    """
    app = ErrorAwareApp.create_app('tests', register_errorhandler=False)

    assert app.error_handlers == {}


def test_exception_error_handler_callback():
    """Ensure the error handler callback works on it's own."""
    app = _create_app(register_error_handlers=False)

    class ErrorPageException(AppException):
        """Implements a small error page for testing."""

        def error_page(self):
            return self.message

    msg = 'foo'
    level = 'danger'
    code = 451
    with app.test_client() as client:
        # just give me a request context to work with
        _ = client.get('/redirected')

        exc = AppException(flash_message=msg, flash_level=level)
        res = AppException.errorhandler_callback(exc)

        assert res is None
        assert '_flashes' in session
        assert session['_flashes'].pop() == (level, msg)

        exc = AppException(redirect='redir_method',
                           redirect_args={'foo': 'bar'})
        res = AppException.errorhandler_callback(exc)
        expected = redirect(url_for('redir_method', foo='bar'))
        assert res.headers == expected.headers
        assert res.data == expected.data
        assert res.status_code == expected.status_code

        exc = ErrorPageException(msg, status_code=code)
        res = AppException.errorhandler_callback(exc)
        assert res == (msg, code)


def test_exception_error_handler_custom_callback():
    """Ensure a custom callback gets installed correctly."""
    app = _create_app(register_error_handlers=False)

    content = b'test'
    flash_level = 'danger'

    class TestException(AppException):
        """Reimplement the errorhandler_callback."""

        @classmethod
        def errorhandler_callback(cls, exc):
            """Return static data, please."""
            return content

    handler_mock = mock.patch.object(TestException,
                                     'errorhandler_callback',
                                     wraps=TestException.errorhandler_callback)
    @app.route('/trigger_test')
    def trigger():
        """Trigger the exception we're testing."""
        raise TestException(flash_message=content)

    @app.route('/trigger_app')
    def trigger_stock():
        """Trigger the stock exception to ensure it doesn't cause a run."""
        raise AppException(flash_message=content, flash_level=flash_level)

    @app.route('/trigger_exc')
    def trigger_exc():
        """Raise a standard exception."""
        raise Exception("Fail")

    try:
        errorhandler_cb = handler_mock.start()

        TestException.register_errorhandler(app)
        AppException.register_errorhandler(app)

        with app.test_client() as client:
            assert errorhandler_cb.call_count == 0
            res = client.get('/trigger_test')

            assert res.data == content
            assert errorhandler_cb.call_count == 1
            # ensure no flashes were added even though the route passes
            # ``flash_message``
            assert '_flashes' not in session

            res = client.get('/trigger_app')

            assert res.data != content
            assert '_flashes' in session
            assert session['_flashes'].pop() == (flash_level, content)
            assert errorhandler_cb.call_count == 1

            res = client.get('/trigger_exc')
            assert res.status_code == 500
            assert res.data == STANDARD_FLASK_500
    finally:
        handler_mock.stop()
