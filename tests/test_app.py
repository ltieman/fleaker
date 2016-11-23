# ~*~ coding: utf-8 ~*~

"""
tests.test_app
~~~~~~~~~~~~~~

Basic tests for the main App instance.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import flask
import fleaker


def _app_asserts(app):
    assert app
    assert isinstance(app, flask.Flask)
    assert not app.debug
    assert app.import_name == __name__

def test_basic_creation():
    """Ensure we can create an app with no frills."""
    app = fleaker.App(__name__)
    _app_asserts(app)

def test_creation_with_kwargs():
    """Ensure we're passing kwargs in properly."""
    kwargs = {
        'static_url_path': '/mystatics',
        'template_folder': '/mytemplates',
        'instance_path': '/my/instance',
        'instance_relative_config': True,
        'root_path': '/a/path',
    }
    app = fleaker.App(__name__, **kwargs)

    _app_asserts(app)

    # this doesn't get stored on the app object, so skip it.
    del kwargs['instance_relative_config']

    for key in kwargs:
        assert kwargs[key] == getattr(app, key)
