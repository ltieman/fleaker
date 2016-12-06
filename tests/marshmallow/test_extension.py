# ~*~ coding: utf-8 ~*~
"""
tests.marshmallow.test_extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests for the :class:`MarshmallowAwareApp` to ensure that it will properly
register the extension and can be used, as well as testing the top level
schema.
"""

import pytest

from flask_marshmallow import fields

from fleaker import Schema
from fleaker.marshmallow import MarshmallowAwareApp, marsh


SERVER_NAME = 'localhost'

def _create_app():
    """Create the app for testing."""
    app = MarshmallowAwareApp.create_app('tests.marshmallow')
    app.config['SERVER_NAME'] = SERVER_NAME

    @app.route('/test')
    def test():
        """Test route for Flask URL generation."""
        return b'test'

    return app


def test_marshmallow_extension_creation():
    """Ensure creating the MM Aware app registers the extension."""
    app = _create_app()

    # now check for the proper extension
    assert 'flask-marshmallow' in app.extensions
    assert app.extensions['flask-marshmallow'] is marsh


def test_marshmallow_extension_url_for():
    """Ensure that the UrlFor field with Flask-Marshmallow works."""
    app = _create_app()

    class TestSchema(Schema):
        """Only has a link field"""
        link = fields.UrlFor('test', _external=False)
        ext_link = fields.UrlFor('test', _scheme='https', _external=True)

    schema = TestSchema()
    
    # not in an app context, should fail
    with pytest.raises(RuntimeError):
        schema.dump({})

    with app.app_context():
        data = schema.dump({}).data

        assert data['link'] == '/test'
        assert data['ext_link'] == 'https://{}/test'.format(SERVER_NAME)
