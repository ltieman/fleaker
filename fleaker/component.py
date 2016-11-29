# ~*~ coding: utf-8 ~*~
"""
fleaker.component
~~~~~~~~~~~~~~~~~

The Fleaker Component is the core building block for your Fleaker Applications.
Instead of placing business or complex logic into a model, you should instead
place it in a Component that uses that Model.

The goal of Components is to be reusable in any context; to support
pluggability and abstraction, i.e., in case you ever need to swap your ORM; and
to make your Models thinner.

The Fleaker Component is not much more than a simple object for you to extend
and populate. However, this object does provide helper methods for storing app
state, grabbing configuration, storing a context, and so forth.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from flask import current_app
from werkzeug.datastructures import ImmutableDict

from ._compat import text_type
from .constants import DEFAULT_DICT


class Component(object):
    """The :class:`Component` class is the main source of Business Logic in
    a Fleaker application. Instead of placing complex, critical logic in Models
    or utils, which are historically hard to understand, find, and organize, it
    goes into a centralized class specific to a given Business Domain or
    Object.

    For example, if you are creating a simple Twitter clone, you would have
    a Component for Users, Tweets, and the Timeline. These components would
    abstract away all database usage, all external API interactions, all
    validation, etc. This allows you to have small Models and Views and makes
    your code reusable, so when that PM asks you to create a User from the
    commandline, it's a simple task instead of a large refactor.

    The other feature of note present in Fleaker Components is the ``context``.
    You can think of the ``context`` as a dictionary to hold data local to the
    current request or action, such as pagination data or the current User. The
    general goal of the context is to promote Dependency Injection and
    Separation of Concerns. Instead of having your Component interact with the
    :class:`werkzeug.wrappers.Request` directly, you can extract information
    from it in the View method and pass it down. This prevents your Component
    from referencing the ``Request`` *at all*, removing the need for
    troublesome mocks or context managers when trying to do simple tasks.

    Conceptually, Fleaker Components work like Flask extensions. They are setup
    with the ``init_app`` pattern, allowing one constructed component to work
    with N number of Apps running side by side. That is roughly all the core
    Fleaker Component gives you, in addition to some helper methods. The rest
    of the magic is up to you to implement!

    Attributes:
        context (werkzeug.datastructures.ImmutableDict): Contextual information
            that is supplied to this component. The attribute is guaranteed to
            always be a ``dict`` like object, but the values within should
            **never** be relied upon, as all values contained therein are
            optional. Also, this attribute is immutable because the component
            should **never** be able to modify the values within the
            ``context``.
    """
    _context = DEFAULT_DICT

    def __init__(self, app=None, context=DEFAULT_DICT):
        """Eager constructor for the :class:`Component` class.

        Keyword Args:
            app (flask.Flask, optional): The Application to base this Component
                upon. Useful for app wide singletons.
            context (dict, optional): The contextual information to supply to
                this component.
        """
        self._app = app
        self.context = context

        if app is not None:
            self.init_app(app, context=context)

    def init_app(self, app, context=DEFAULT_DICT):
        """Lazy constructor for the :class:`Component` class.

        This method will allow the component to be used like a Flask
        extension/singleton.

        Args:
            app (flask.Flask): The Application to base this Component upon.
                Useful for app wide singletons.

        Keyword Args:
            context (dict, optional): The contextual information to supply to
                this component.
        """
        self.update_context(context, app=app)

    @property
    def context(self):
        """Return the current context for the component.

        Returns:
            werkzeug.datastructures.ImmutableDict: The current ``context`` that
                this component is being used within.
        """
        # @TODO Figure out how to get extension style contexts working
        # ctx = STACK.top
        #
        # if ctx is not None:
        #     key = self._get_context_name()
        #
        #     if not hasattr(ctx, key):
        #         setattr(ctx, key, DEFAULT_DICT)
        #
        #     return getattr(ctx, key)
        #
        # return DEFAULT_DICT

        return self._context

    @context.setter
    def context(self, context):
        """Replace the context of the component with a new one.

        Args:
            context (dict): The dictionary to set the ``context`` to.
        """
        self.update_context(context)

    def update_context(self, context, app=None):
        """Replace the component's context with a new one.

        Args:
            context (dict): The new context to set this component's context to.

        Keyword Args:
            app (flask.Flask, optional): The app to update this context for. If
                not provided, the result of ``Component.app`` will be used.
        """
        # @TODO Figure out how to get the extension style context working
        # ctx = STACK.top
        #
        # if ctx is not None:
        #     key = self._get_context_name(app=app)
        #     setattr(ctx, key, ImmutableDict(context))

        self._context = ImmutableDict(context)

    def clear_context(self, app=None):
        """Clear the component's context.

        Keyword Args:
            app (flask.Flask, optional): The app to clear this component's
                context for. If omitted, the value from ``Component.app`` is
                used.
        """
        # @TODO Figure out how to get the extension style context working
        # ctx = STACK.top
        #
        # if ctx is not None:
        #     key = self._get_context_name(app=app)
        #     setattr(ctx, key, DEFAULT_DICT)

        self._context = DEFAULT_DICT

    @property
    def app(self):
        """Internal method that will supply the app to use internally.

        Returns:
            flask.Flask: The app to use within the component.

        Raises:
            RuntimeError: This raised if no app was provided to the component
                and the method is being called outside of an application
                context.
        """
        app = self._app or current_app

        # This is the best way to check if current_app is a proxy.
        if not dir(app):
            raise RuntimeError("This component hasn't been initialized yet "
                               "and an app context doesn't exist.")

        # If current_app is the app, this must be used in order for their IDs
        # to be the same, as current_app will wrap the app in a proxy.
        if hasattr(app, '_get_current_object'):
            app = app._get_current_object()

        return app

    @property
    def config(self):
        """Return the component's app's config.

        Returns:
            dict: The App's config.
        """
        return self.app.config

    def _get_context_name(self, app=None):
        """Generate the name of the context variable for this component & app.

        Because we store the ``context`` in the app's context so the component
        can be used across multiple apps, we cannot store the context on the
        instance itself. This function will generate a unique and predictable
        key in which to store the context.

        Returns:
            str: The name of the context variable to set and get the context
                from.
        """
        # @TODO Determine if this is needed after we figure out how to store
        # the context.
        # elements = [
        #     self.__class__.__name__,
        #     'context',
        #     text_type(id(self))
        # ]
        #
        # if app:
        #     elements.append(text_type(id(app)))
        # else:
        #     try:
        #         elements.append(text_type(id(self.app)))
        #     except RuntimeError:
        #         pass
        #
        # return '_'.join(elements)
