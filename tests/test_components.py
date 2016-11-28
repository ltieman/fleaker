# ~*~ coding: utf-8 ~*~
"""
tests.test_components
~~~~~~~~~~~~~~~~~~~~~

Tests for the Fleaker Component tool.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import pytest

from fleaker import App, Component


def _create_app():
    """Helper function to create the basic app for testing."""
    app = App(__name__)

    app.configure({
        'FOO': 'BAR'
    })

    return app


def test_component_creation_with_app():
    """Ensure we can create a Component with an app."""
    app = _create_app()

    comp = Component(app=app)

    assert comp.app == app
    assert comp._app is app
    assert comp.config['FOO'] == 'BAR'


def test_component_creation_with_init_app():
    """Ensure we can create a Component without an app."""
    app = _create_app()

    comp = Component()

    comp.init_app(app)

    assert comp.app == app
    assert comp._app is None
    assert comp.config['FOO'] == 'BAR'

    # now test with some context
    ctx = {
        'current_user': None,
        'limit': 10,
        'offset': 10,
        'foo': 'bar',
    }

    comp = Component()
    comp.init_app(app, context=ctx)

    assert comp.app == app
    assert comp.context == ctx
    assert comp._context is None


def test_component_context():
    """Ensure the context element of a Component works."""
    app = _create_app()

    ctx = {
        'current_user': None,
        'limit': 10,
        'offset': 10,
        'foo': 'bar',
    }

    comp = Component(app=app, context=ctx)

    assert comp.context
    assert comp.context == ctx
    assert comp._context == ctx

    # now replace the context in place
    new_ctx = {
        'baz': 'qux',
        'limit': 20,
        'new_key': 'new'
    }
    comp.update_context(new_ctx)

    assert comp.context == new_ctx
    assert comp._context == new_ctx
    assert 'current_user' not in comp.context
    assert 'offset' not in comp.context
    assert comp.context['limit'] == 20
    assert comp.context['new_key'] == 'new'


def test_context_with_init_app():
    """Ensure context works with init_app"""
    import pytest
    pytest.fail()

    # @TODO: Bring over parts of the test_multiple_apps stuff to test this
    # without an explicit app


def test_component_implicit_current_app():
    """Ensure that a component without app knowledge falls back to current_app
    """
    app = _create_app()

    comp = Component()

    with app.test_request_context('/'):
        assert comp.app == app

    # and with no proxies bound, give me a RuntimeError
    with pytest.raises(RuntimeError):
        assert comp.app != app


def test_clear_context():
    """Ensure we can clear the context"""
    app = _create_app()

    ctx = {
        'ctxkey': 'bar',
    }

    comp = Component(app=app, context=ctx)

    assert comp.context == ctx

    comp.clear_context()

    assert comp.context == {}


def test_clear_context_with_init_app():
    """Ensure clear_context works with init_app"""
    import pytest
    pytest.fail()

    # @TODO: Bring over the tail end of test_multiple_apps to test this


def test_multiple_apps():
    """Ensure components work with multiple apps at once."""
    # @TODO: Break this test up and make her smaller
    app1 = _create_app()
    app1_context = {
        'is_app1': True,
        'app1_key': 'bar',
    }

    app2 = App('test_app_2')
    app2_context = {
        'is_app2': True,
        'app2_key': 'foo',
    }

    class TestComponent(Component):
        pass

    comp = TestComponent()

    # with app1.test_request_context():
    with app1.app_context():
        comp.init_app(app1, context=app1_context)
        assert comp.app is app1
        assert comp._app is None
        assert comp.context == app1_context
        assert 'is_app2' not in comp.context

    with app2.app_context():
        comp.init_app(app2, context=app2_context)
        assert comp.app is app2
        assert comp._app is None
        assert comp.context == app2_context
        assert 'is_app1' not in comp.context

    # now update the context
    new_app1_context = {
        'is_app1': 'foo',
        'new_key': 'bar',
    }
    new_app2_context = {
        'is_app2': 'baz',
        'new_key2': 'qux',
    }

    comp.update_context(new_app1_context, app=app1)
    comp.update_context(new_app2_context, app=app2)

    # if no app is registered as the primary app AND there is no current_app,
    # then this should fail enitrely
    with pytest.raises(RuntimeError):
        comp.update_context({'fail': True})

    with app1.test_request_context():
        assert comp.context == new_app1_context
        assert comp._context is None
        assert 'app1_key' not in comp.context
        assert comp.context['new_key'] == 'bar'

        with app2.test_request_context():
            assert comp.context == new_app2_context
            assert comp._context is None
            assert 'app2_key' not in comp.context
            assert comp.context['new_key2'] == 'qux'

    fresh_context = {
        'is_app1': 'yes',
        'naked_key': 'bar',
    }

    # if we have a current_app, then update_context should work without an app
    # arg
    with app1.test_request_context():
        comp.update_context(fresh_context)

        assert comp.context == fresh_context
        assert comp.context['naked_key'] == 'bar'
        assert 'new_key' not in comp.context

    # this should persist outside the with
    with app1.test_request_context():
        assert comp.context == fresh_context
        assert comp.context['naked_key'] == 'bar'
        assert 'new_key' not in comp.context

    # this should not pollute the context for other apps
    with app2.test_request_context():
        assert comp.context == new_app2_context
        assert 'naked_key' not in comp.context

    # if we have a current app and provide an explicit app, there should not be
    # a conflict
    fresh_context2 = {
        'is_app2': 'si',
        'neweset_key': 'fresh',
    }
    with app1.test_request_context():
        comp.update_context(fresh_context2, app=app2)

        # we still have app1 active though, so we shouldn't get the new context
        assert comp.context == fresh_context
        assert 'newest_key' not in comp.context
        assert comp.context['naked_key'] == 'bar'

    with app2.test_request_context():
        assert comp.context == fresh_context2
        assert comp.context['newest_key'] == 'fresh'
        assert 'naked_key' not in comp.context

    # can't do this without an explicit app
    with pytest.raises(RuntimeError):
        comp.clear_context()

    with app1.test_request_context():
        comp.clear_context()
        assert comp.context == {}

    # app2 should be fine
    with app2.test_request_context():
        assert comp.context == fresh_context2

    # should be able to clear outside and it persist
    comp.clear_context(app=app2)
    with app2.test_request_context():
        assert comp.context == {}
