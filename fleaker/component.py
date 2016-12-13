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

from flask import appcontext_pushed, appcontext_popped, current_app
from werkzeug.datastructures import ImmutableDict
from werkzeug.local import Local

from ._compat import text_type
from .constants import DEFAULT_DICT
from .missing import MissingDictSentinel
from .utils import in_app_context

# two small helpers to track some module specific info; _CONTEXT_LOCALS is
# a Local where we'll store all contexts for all possible apps;
# _CONTEXT_CALLBACK_MAP is a small map that lets us track which apps have
# already had their callbacks properly applied
_CONTEXT_LOCALS = Local()
_CONTEXT_CALLBACK_MAP = {}
_CONTEXT_MISSING = MissingDictSentinel()


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
    :class:`~werkzeug.wrappers.Request` directly, you can extract information
    from it in the View method and pass it down. This prevents your Component
    from referencing the :class:`~werkzeug.wrappers.Request` *at all*, removing
    the need for troublesome mocks or context managers when trying to do simple
    tasks.

    Conceptually, Fleaker Components work like Flask extensions. They are setup
    with the ``init_app`` pattern, allowing one constructed component to work
    with N number of Apps running side by side. That is roughly all the core
    Fleaker Component gives you, in addition to some helper methods. The rest
    of the magic is up to you to implement!

    Attributes:
        context (werkzeug.datastructures.ImmutableDict):
            Contextual information that is supplied to this component. The
            attribute is guaranteed to always be a ``dict`` like object, but
            the values within should **never** be relied upon, as all values
            contained therein are optional. Also, this attribute is immutable
            because the component should **never** be able to modify the values
            within the ``context``.
    """
    _context = _CONTEXT_MISSING

    def __init__(self, app=None, context=_CONTEXT_MISSING):
        """Eager constructor for the :class:`Component` class.

        Keyword Args:
            app (flask.Flask, optional): The Application to base this Component
                upon. Useful for app wide singletons.
            context (dict, optional): The contextual information to supply to
                this component.
        """
        # the user has passed an app, but did not pass a context, so default it
        # out for them
        if app is not None and context is _CONTEXT_MISSING:
            context = DEFAULT_DICT

        self._app = app
        self._context = context

        if app is not None:
            self.init_app(app, context=_CONTEXT_MISSING)

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
        if context is not _CONTEXT_MISSING:
            self.update_context(context, app=app)

        # do not readd callbacks if already present; and if there's no context
        # present, there's no real need to add callbacks
        if (app not in _CONTEXT_CALLBACK_MAP
                and context is not _CONTEXT_MISSING):
            key = self._get_context_name(app=app)
            self._context_callbacks(app, key, original_context=context)

    @staticmethod
    def _context_callbacks(app, key, original_context=_CONTEXT_MISSING):
        """Register the callbacks we need to properly pop and push the
        app-local context for a component.

        Args:
            app (flask.Flask): The app who this context belongs to. This is the
                only sender our Blinker signal will listen to.
            key (str): The key on ``_CONTEXT_LOCALS`` that this app's context
                listens to.

        Kwargs:
            original_context (dict): The original context present whenever
                these callbacks were registered. We will restore the context to
                this value whenever the app context gets popped.

        Returns:
            (function, function): A two-element tuple of the dynamic functions
                we generated as appcontext callbacks. The first element is the
                callback for ``appcontext_pushed`` (i.e., get and store the
                current context) and the second element is the callback for
                ``appcontext_popped`` (i.e., restore the current context to
                to it's original value).
        """
        def _get_context(dummy_app):
            """Set the context proxy so that it points to a specific context.
            """
            _CONTEXT_LOCALS.context = _CONTEXT_LOCALS(key)  # pylint: disable=assigning-non-slot

        def _clear_context(dummy_app):
            """Remove the context proxy that points to a specific context and
            restore the original context, if there was one.
            """
            del _CONTEXT_LOCALS.context

            if original_context is not _CONTEXT_MISSING:
                setattr(_CONTEXT_LOCALS, key, original_context)

        # store for later so Blinker doesn't remove these listeners and so we
        # don't add them twice
        _CONTEXT_CALLBACK_MAP[app] = (_get_context, _clear_context)

        # and listen for any app context changes
        appcontext_pushed.connect(_get_context, app)
        appcontext_popped.connect(_clear_context, app)

        return (_get_context, _clear_context)

    @property
    def context(self):
        """Return the current context for the component.

        Returns:
            werkzeug.datastructures.ImmutableDict: The current ``context`` that
                this component is being used within.
        """
        if self._context is not _CONTEXT_MISSING:
            return self._context

        return _CONTEXT_LOCALS.context

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
        if (app is None and self._context is _CONTEXT_MISSING
                and not in_app_context()):
            raise RuntimeError("Attempted to update component context without"
                               " a bound app context or eager app set! Please"
                               " pass the related app you want to update the"
                               " context for!")

        if self._context is not _CONTEXT_MISSING:
            self._context = ImmutableDict(context)
        else:
            key = self._get_context_name(app=app)
            setattr(_CONTEXT_LOCALS, key, ImmutableDict(context))

    def clear_context(self, app=None):
        """Clear the component's context.

        Keyword Args:
            app (flask.Flask, optional): The app to clear this component's
                context for. If omitted, the value from ``Component.app`` is
                used.
        """
        if (app is None and self._context is _CONTEXT_MISSING
                and not in_app_context()):
            raise RuntimeError("Attempted to clear component context without"
                               " a bound app context or eager app set! Please"
                               " pass the related app you want to update the"
                               " context for!")

        if self._context is not _CONTEXT_MISSING:
            self._context = DEFAULT_DICT
        else:
            key = self._get_context_name(app=app)
            setattr(_CONTEXT_LOCALS, key, DEFAULT_DICT)

    @property
    def app(self):
        """Internal method that will supply the app to use internally.

        Returns:
            flask.Flask: The app to use within the component.

        Raises:
            RuntimeError: This is raised if no app was provided to the
                component and the method is being called outside of an
                application context.
        """
        app = self._app or current_app

        if not in_app_context(app):
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

        Because we store the ``context`` in a Local so the component
        can be used across multiple apps, we cannot store the context on the
        instance itself. This function will generate a unique and predictable
        key in which to store the context.

        Returns:
            str: The name of the context variable to set and get the context
                from.
        """
        elements = [
            self.__class__.__name__,
            'context',
            text_type(id(self)),
        ]

        if app:
            elements.append(text_type(id(app)))
        else:
            try:
                elements.append(text_type(id(self.app)))
            except RuntimeError:
                pass

        return '_'.join(elements)
