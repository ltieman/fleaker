# ~*~ coding: utf-8 ~*~
"""
fleaker.marshmallow.extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Fleaker Marshmallow module provides an extension that hooks in to the app
to register Flask-Marshmallow_. While this extension isn't strictly needed for
Marshmallow to work, it does provide some really useful fields, like being able
to generate Flask URLs.

Attributes:
    marsh (flask_marshmallow.Marshmallow): The initialized Flask Marshmallow
        extension. This will be a part of :class:`fleaker.marshmallow.Schema`
        so all extensions inheriting from it will have the Flask context
        inserted into them.

.. _Flask-Marshmallow: https://flask-marshmallow.readthedocs.io

"""

from flask_marshmallow import Marshmallow

from fleaker.base import BaseApplication


# Define a Flask extension for Marshmallow. This will be be init'd in the app
# factory.
marsh = Marshmallow()


class MarshmallowAwareApp(BaseApplication):
    """Fleaker application mixin that will automatically register the Flask
    Marshmallow extension.
    """

    @classmethod
    def post_create_app(cls, app, **settings):
        """Automatically register and init the Flask Marshmallow extension.

        Args:
            app (flask.Flask): The application instance in which to initialize
                Flask Marshmallow upon.

        Kwargs:
            settings (dict): The settings passed to this method from the
                parent app.

        Returns:
            flask.Flask: The Flask application that was passed in.
        """
        super(MarshmallowAwareApp, cls).post_create_app(app, **settings)

        marsh.init_app(app)

        return app
