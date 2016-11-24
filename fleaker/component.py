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


class Component(object):
    """The :class:`Component` class is the main source of Business Logic in
    a Fleaker application. Instead of placing complex, critical logic in Models
    or utils, which are historically hard to understand, find, and organize, it
    goes into a centralized class specific to a given Business Domain or Object.

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
    """
    
    def __init__(self, app=None, context=None):
        self._app = app
        self._context = context

        if app is not None:
            self.init_app(app)

    def init_app(self, app, context=None):
        pass
