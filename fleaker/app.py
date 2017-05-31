# ~*~ coding: utf-8 ~*~
"""
    fleaker.app
    ~~~~~~~~~~~

    This module implements various applications or middlewares that can be
    strung together to create your application.

    :copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from .base import BaseApplication
from .config import MultiStageConfigurableApp
from .json import FleakerJSONApp
from .logging import LoggingAwareApp
from .marshmallow import MarshmallowAwareApp
from .orm import ORMAwareApp
from .test_client import FlaskClientAwareApp


class App(MultiStageConfigurableApp, MarshmallowAwareApp, FleakerJSONApp,
          ORMAwareApp, FlaskClientAwareApp, LoggingAwareApp, BaseApplication):
    """The :class:`App` class is the primary entrypoint for using Fleaker and
    is a simple WSGI Application. In it's simplest form, you can think of
    :class:`App` as roughly equivalent to :class:`flask.Flask`. On top of
    everything that the standard :class:`~flask.Flask` provides, the Fleaker
    :class:`App` also provides convenience functions for setting up common
    patterns, such as settings configuration, automatic blueprint discovery,
    registering the login manager, and many other tasks.

    Like :class:`~flask.Flask`, it is passed the name of the module or package
    of the application. This name is reused frequently in order to resolve
    relative imports in helper methods and to locate generic resources. It
    accepts all of the same args and kwargs as :class:`~flask.Flask`.

    You can easily create an instance of :class:`App`, wherever you choose,
    like so::

        from fleaker import App
        app = App(__name__)

    :class:`App` is really just an extended and supercharged version of
    :class:`~flask.Flask`, so anything available to your standard Flask app is
    available in :class:`App`.

    :class:`App` is largely made of individual mixins so see
    :ref:`default-mixins` for more information. Additionally, :class:`App`
    extends the basic :class:`~flask.Flask`, so see it's documentation for more
    information on members and methods.

    .. versionadded:: 0.1.0
       The :class:`App` class has existed since Fleaker was conceived.
    """

    def __init__(self, import_name, **kwargs):
        super(App, self).__init__(import_name, **kwargs)

        # @TODO: What was the rest of this supposed to do?
