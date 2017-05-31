# ~*~ coding: utf-8 ~*~
"""
    tests.conftest
    ~~~~~~~~~~~~~~

    :copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details
"""

import os

import pytest

from fleaker import App, MISSING
from fleaker._compat import text_type


@pytest.fixture(autouse=True)
def update_environment(request):
    """Update the environment based on what is provided in marks and then tear
    it all down.

    Provide your environment overrides in the ``environ`` marker as a kwarg.
    """
    updates = request.node.get_marker('environ')
    originals = {}

    if not updates:
        yield
        return

    updates = updates.kwargs

    for key, val in updates.items():
        originals[key] = os.environ.get(key, MISSING)
        os.environ[key] = text_type(val)

    yield

    for key, val in originals.items():
        if val is MISSING:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


@pytest.fixture
def app():
    """Pytest-Flask fixture that will push a Fleaker app context to the stack.

    This fixture can be used to test methods on the Fleaker app instance easily
    and should be used where possible because playing around with application
    contexts is not fun at all. Granted, if you need to create your own
    extended App for a specific test... this can't help you.

    Returns:
        fleaker.App: An instantiated Flask application.
    """
    app = App.create_app(__name__)
    app.configure({})

    return app
