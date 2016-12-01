# ~*~ coding: utf-8 ~*~
"""
fleaker.base
~~~~~~~~~~~~~

This module provides the Base Application for Fleaker and supporting functions.

The Base Application is the single Flask Application that ALL other mixins
inherit from. For the most part, it merely defines the hooks that all mixins
need to implement for the standard Fleaker app to work.

We MUST define these hooks to make Python happy. The location of this is also
chosen to make Python happy, by placing it here instead of in ``fleaker.app``,
we avoid circular imports. Huzzah!

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import inspect

from copy import deepcopy

from flask import Flask

from ._compat import iteritems


class BaseApplication(Flask):
    """The :class:`BaseApplication` is the parent class for all mixins within
    Fleaker, and for the standard Fleaker app.

    All this class does is define some small hook functions, which only return
    their input by default. This class exists so that all inherited classes
    have a nice, predictable base set of methods to use.

    This is **NOT** something the average Fleaker developer will use. If you're
    looking for Fleaker's standard app, please see :class:`fleaker.app.App`.
    However, if you're interested in writing a new mixin or extension for
    Fleaker, then this is the right place for you! Your new mixin class should
    extend this and from there you're free to do what you want.

    A quick sample:

    .. code:: python

        from fleaker.base import BaseApplication


        class MyAwesomeExtension(BaseApplication):
            \"\"\"Prints hello after the app is made!\"\"\"

            @classmethod
            def post_create_hook(cls, app, **settings):
                # ensure that you have your super call!
                super(MyAwesomeExtension, cls).post_create_hook(
                    app,
                    **settings
                )

                # do your logic here!
                print("hello")

                # ALWAYS return the app in this hook.
                return app
    """
    # Cache for the argspec from :class:`flask.Flask.__init__` that we'll need
    # in a bit.
    _flask_init_argspec_cache = None

    @classmethod
    def create_app(cls, import_name, **settings):
        """Create a standard Fleaker web application.

        This is the main entrypoint for creating your Fleaker application.
        Instead of defining your own app factory function, it's preferred that
        you use :meth:`create_app`, which is responsible for automatically
        configuring extensions (such as your ORM), parsing setup code for
        mixins, and calling relevant hooks (such as to setup logging).

        Usage is easy:

        .. code:: python

            from fleaker import App

            def my_create_app():
                app = App.create_app(__name__)
                return app

        And the rest works like a normal Flask app with application factories
        setup!

        .. versionadded:: 0.1.0
           This has always been the preferred way to create Fleaker
           Applications.
        """
        settings = cls.pre_create_app(**settings)

        # now whitelist the settings
        flask_kwargs = cls._whitelist_standard_flask_kwargs(settings)

        app = cls(import_name, **flask_kwargs)
        return cls.post_create_app(app, **settings)

    @classmethod
    def _whitelist_standard_flask_kwargs(cls, kwargs):
        """Whitelist a dictionary of kwargs to remove any that are not valid
        for Flask's ``__init__`` constructor.

        Since many Fleaker app mixins define their own kwargs for use in
        construction and Flask itself does not accept ``**kwargs``, we need to
        whitelist anything unknown.

        Uses the proper argspec from the :meth:`flask.Flask.__init__` so it
        should handle all args.

        Args:
            kwargs (dict): The dictionary of kwargs you want to whitelist.

        Returns:
            dict: The whitelisted dictionary of kwargs.
        """
        # prevent any copy shenanigans from happening
        kwargs = deepcopy(kwargs)

        if not cls._flask_init_argspec_cache:
            cls._flask_init_argspec_cache = inspect.getargspec(Flask.__init__)

        return {key: val for key, val in iteritems(kwargs)
                if key in cls._flask_init_argspec_cache.args}

    @classmethod
    def post_create_app(cls, app, **settings):
        """Run any logic that needs to be done strictly after the app has been
        made.

        The Post Create Hook will be run strictly after :meth:`create_app` has
        finished running. It will be given the App that was created and it is
        expected to return an app of some sort, ideally the one provided. It
        will also be given all kwargs passed to :meth:`create_app` for
        configuration purposes.

        The goal of the Post Create Hook is to allow Fleaker extensions to do
        any logic that requires an App Instance, such as initializing Standard
        Flask Extensions (calling ``init_app``), replacing the WSGI App with
        some new middleware, or even replacing the entire App itself (NOT
        recommended, but doable).

        Feel free to extend this in your child classes, matching this spec.

        .. admonition:: Make Sure You Call ``super``!

            A failure to call `super` in a hook method, such as the Post Create
            Hook, is likely to break your **entire Fleaker App chain**! Make
            sure the very first, or very last, thing that your hook does is
            call `super`!
        """
        return app

    @classmethod
    def pre_create_app(cls, **settings):
        """Run any logic that needs to be done strictly before the app has been
        made.

        The Pre Create Hook will be run immediately before :meth:`create_app`
        is run. It will be given the kwargs that were passed to
        :meth:`create_app` as it's kwargs. It is expected to return
        a dictionary of kwargs that will be passed to the actual App
        ``__init__`` call and to the :meth:`post_create_app` hook.

        Basically, this lets you hook in and parse or change settings
        dynamically. That's it's only goal and what it can do is up to you!

        .. admonition:: Make Sure You Call ``super``!

            A failure to call `super` in a hook method, such as the Pre Create
            Hook, is likely to break your **entire Fleaker App chain**! Make
            sure the very first, or very last, thing that your hook does is
            call `super`!
        """
        return settings

    def add_post_configure_callback(self, func):
        """Raise an error when a developer attempts to add a post configure
        callback.

        Post Configure Callbacks are only implemented on the
        MultiStageConfigurableApp, but I know one day someone will forget that
        and this method will help them out.

        Args:
            func (function): Function we would register, if we could.

        Raises:
            NotImplementedError: Always raises this because this class doesn't
                support this concept.
        """
        raise NotImplementedError("`post_configure` callbacks are only "
                                  "implemented on the "
                                  "MultiStageConfigurableApp! Ensure that "
                                  "mixin is present!")
