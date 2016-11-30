# ~*~ coding: utf-8 ~*~
"""
tests.test_components
~~~~~~~~~~~~~~~~~~~~~

Tests for the Fleaker Component tool.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import pytest

from fleaker import App, Component, DEFAULT_DICT, MISSING


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

    assert comp.app is comp._app is app
    assert comp.config['FOO'] == 'BAR'


def test_component_creation_with_init_app():
    """Ensure we can create a Component without an app."""
    app = _create_app()
    comp = Component()
    comp.init_app(app)

    with app.app_context():
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

        # @TODO: detect that this is already registered and update the default
        # context...
        comp.init_app(app, context=ctx)

        assert comp.app == app
        assert comp.context == ctx


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


def test_component_context_no_default_eager_app():
    """Ensure that context works without a default context."""
    app = _create_app()

    comp = Component(app=app)

    new_ctx = {
        'foo': 'bar'
    }

    assert comp._context is DEFAULT_DICT
    assert comp.context is DEFAULT_DICT

    comp.update_context(new_ctx)

    assert comp.context == new_ctx
    assert comp._context == new_ctx

    comp.clear_context()

    assert comp.context is DEFAULT_DICT
    assert comp._context is DEFAULT_DICT


@pytest.mark.skip("Need time to write this; will fill out later.")
def test_context_with_init_app():
    """Ensure context works with init_app"""
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


@pytest.mark.skip("Need time to write this; will fill out later.")
def test_clear_context_with_init_app():
    """Ensure clear_context works with init_app"""
    # @TODO: Bring over the tail end of test_multiple_apps to test this
    pytest.fail()


def test_component_raises_when_no_app():
    """Ensure that Component.app raises if nothing is present."""
    err_msg = ("This component hasn't been initialized yet and an app context"
               " doesn't exist.")
    with pytest.raises(RuntimeError, message=err_msg):
        Component().app


def test_multiple_apps():
    """Ensure components work with multiple apps at once."""
    # @TODO: Break this test up and make her smaller
    app1 = _create_app()
    app1_context = {
        'is_app1': True,
        'app1_key': 'bar',
    }
    app1.config['IS_APP1'] = True

    app2 = App('test_app_2')
    app2_context = {
        'is_app2': True,
        'app2_key': 'foo',
    }
    app2.config['IS_APP2'] = True

    class TestComponent(Component):
        pass

    comp = TestComponent()
    comp.init_app(app1, context=app1_context)

    with app1.app_context():
        assert comp.app is app1
        assert comp._app is None
        assert comp.context == app1_context
        assert comp._context is MISSING
        assert 'is_app2' not in comp.context
        assert comp.config['IS_APP1']
        assert 'IS_APP2' not in comp.config

    comp.init_app(app2, context=app2_context)

    with app2.app_context():
        assert comp.app is app2
        assert comp._app is None
        assert comp.context == app2_context
        assert comp._context is MISSING
        assert 'is_app1' not in comp.context
        assert comp.config['IS_APP2']
        assert 'IS_APP1' not in comp.config

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

    err_msg = ("Attempted to update component context without a bound app "
               "context or eager app set! Please pass the related app you "
               "want to update the context for!")
    # if no app is registered as the primary app AND there is no current_app,
    # then this should fail enitrely
    with pytest.raises(RuntimeError, message=err_msg):
        comp.update_context({'fail': True})

    with app1.test_request_context():
        assert comp.context == new_app1_context
        assert comp._context is MISSING
        assert 'app1_key' not in comp.context
        assert comp.context['new_key'] == 'bar'

    with app2.test_request_context():
        assert comp.context == new_app2_context
        assert comp._context is MISSING
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

    # this should not influence the other app's context though
    with app2.test_request_context():
        assert comp.context == app2_context
        assert 'naked_key' not in comp.context

    # @TODO: Create a method to update the original context and test that
    # this should persist outside the with
    # with app1.test_request_context():
    #     assert comp.context == fresh_context
    #     assert comp.context['naked_key'] == 'bar'
    #     assert 'new_key' not in comp.context

    # this should not pollute the context for other apps
    # with app2.test_request_context():
    #     assert comp.context == new_app2_context
    #     assert 'naked_key' not in comp.context

    # if we have a current app and provide an explicit app, there should not be
    # a conflict
    fresh_context2 = {
        'is_app2': 'si',
        'neweset_key': 'fresh',
    }
    with app1.test_request_context():
        comp.update_context(fresh_context2, app=app2)

        # we still have app1 active though, so we shouldn't get the new context
        assert comp.context == app1_context
        assert 'newest_key' not in comp.context

    # @TODO: Create a method to update the original context and test that here
    # (the call above to comp.update_context should work)
    # with app2.test_request_context():
    #     assert comp.context == fresh_context2
    #     assert comp.context['newest_key'] == 'fresh'
    #     assert 'naked_key' not in comp.context

    err_msg = ("Attempted to clear component context without a bound app "
               "context or eager app set! Please pass the related app you "
               "want to update the context for!")

    # can't do this without an explicit app
    with pytest.raises(RuntimeError, message=err_msg):
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
