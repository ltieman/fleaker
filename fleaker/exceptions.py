# ~*~ coding: utf-8 ~*~
"""
fleaker.exceptions
~~~~~~~~~~~~~~~~~~

Implements a base exception for the library, provides a base exception for end
developers to import, extend, and reuse, and provides a Composable App for
automatic error handling.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from flask import flash, url_for, redirect

from fleaker import DEFAULT_DICT, MISSING
from fleaker.base import BaseApplication


class FleakerBaseException(Exception):
    """Base class for all Fleaker Exception Classes.

    This Exception should NEVER be thrown under ANY circumstances. It has
    three uses:

        1. As the parent class for :class:`FleakerException`.
        2. As the parent class for :class:`AppException`.
        3. Wrapping blocks of code that could possibly fail due to your app,
           or Fleaker, that you want to handle.

    #1 and #2 have been done at the time of this writing.

    Now, for an explanation. Fleaker implements two base exceptions. The first
    is :class:`FleakerException` which is the base class for all Exceptions
    that Fleaker itself will throw. It is safe to ``except`` anytime you expect
    Fleaker to possibly fail. The second is :class:`AppException` which is an
    exception that an Application Developer is expected to import and reuse as
    their own Application's base exception.

    We surface the :class:`FleakerBaseException` to the end user as
    :class:`AppException` because many of the features in
    :class:`FleakerBaseException` are intended for them to use, such as
    auto-redirects, auto-flash messages, etc. This gives them a very powerful
    base Exception to start building off of. We then reuse this same Exception
    base for :class:`FleakerException` because... why not? Even if Fleaker
    itself won't use most of this, providing the funtionality adds little harm
    and gives us room to grow.

    From there we create two separate Exception hierarchies so that ``except``'s
    are always clean and never collide, e.g., you can ``except
    FleakerException`` and NOT implicitly catch all :class:`AppException`'s with
    it.

    The custom features this base exception provides are:
        1. The ability to specify a status code with your exception.
        2. A small error handler callback method that does the following:
            1. Automatically rollback the database session, unless
               the ``prevent_rollback`` kwarg is ``True``.
            2. Automatically set a flash message of a given level. Message
               comes from the ``flash_message`` kwarg and severity level comes
               from the ``flash_level`` kwarg.
            3. Automatically redirect the client to another route. The route
               should be set via the ``redirect`` kwarg and kwargs for the
               redirect should be set via the ``redirect_args`` kwarg, both are
               passed straight to :func:`flask.url_for`.

    Attributes:
        message (unicode): A message for this specific Exception instance. Can
            be passed as either the first arg, or the ``message`` kwarg.
        status_code (int): The status code that processing of this Exception
            should result in. For example, if this exception indicates an
            Authorization Failure, a 403 is a nice status code to use. This
            will be used in conjunction with :meth:`error_page` to render
            pretty, automatic error pages.
        redirect (unicode): If this is set when initializing the exception, it
            must be the name of a route registered to the application (the
            actual endpoint name). When this hits the global error handler for
            the exception, it can optionally redirect the user to this route.
        redirect_args (dict): This dict of args will be piped directly into
            :func:`~flask.url_for` for the redirect.
        prevent_rollback (bool): By default, if this exception bubbles up to a
            error handler, the DB transaction will be rolled back. If this
            behavior isn't desirable, set this to ``False`` when raising the
            exception.
        flash_message (unicode): If the User is being redirected, this is
            a message we should ``flash`` at them, telling them what happened.
        flash_level (unicode): If a message is being flashed, what level should
            it be? This value should be one that works with
            :func:`flask.flash`'s second argument.
    """

    redirect = MISSING
    redirect_args = DEFAULT_DICT
    prevent_rollback = False
    # @TODO (exc): We should be able to support flashing the exc message as is.
    # Likely adding a ``flash`` kwarg that, when True flashes the default
    # message is a good idea.
    flash_message = False
    flash_level = 'danger'

    def __init__(self, *args, **kwargs):
        """Construct a base Fleaker Exception, accepting optional kwargs to
        control behavior/set context.
        """
        self.redirect = kwargs.pop('redirect', MISSING)
        self.redirect_args = kwargs.pop('redirect_args', DEFAULT_DICT)
        self.prevent_rollback = kwargs.pop('prevent_rollback', False)
        self.flash_message = kwargs.pop('flash_message', False)
        self.flash_level = kwargs.pop('flash_level', 'danger')
        self.status_code = kwargs.pop('status_code', None)
        self.message = kwargs.pop('message', '') or next(iter(args or []), '')

        super(Exception, self).__init__(*args, **kwargs)

    @classmethod
    def errorhandler_callback(cls, exc):
        """This function should be called in the global error handlers. This
        will allow for consolidating of cleanup tasks if the exception
        bubbles all the way to the top of the stack.

        For example, this method will automatically rollback the database
        session if the exception bubbles to the top.

        This is the method that :meth:`register_errorhandler` adds as an
        errorhandler. See the documentation there for more info.

        Args:
            exc (FleakerBaseException):
                The exception that was thrown that we are to handle.
        """
        # @TODO (orm, exc): Implement this when the ORM/DB stuff is done
        # if not exc.prevent_rollback:
        #     db.session.rollback()

        if exc.flash_message:
            flash(exc.flash_message, exc.flash_level)

        if exc.redirect is not MISSING:
            return redirect(url_for(exc.redirect, **exc.redirect_args))

        error_result = exc.error_page()

        if error_result is not None:
            return error_result, exc.status_code or 500

    @classmethod
    def register_errorhandler(cls, app):
        """Register the standard error handler for this exception on this App.

        This will set :meth:`errorhandler_callback` as an error handler for
        this exception. This means all exceptions that inherit from this class
        will be caught by that error handler.

        This method does nothing other than registration and the actual
        implementation of the callback is found in
        :meth:`errorhandler_callback`. If you want a custom exception derived
        from this exception to run a custom callback, please override
        :meth:`errorhandler_callback`, and continue to use this function to
        register.

        Example usage:

        .. code:: python

            from fleaker import AppException

            def create_app():
                app = fleaker.App(__name__)

                # this will register the standard callback
                AppException.register_errorhandler(app)

                class MyException(AppException):
                    \"\"\"Has a custom handler callback.\"\"\"

                    @classmethod
                    def errorhandler_callback(cls, exc):
                        \"\"\"Custom error handler that greets the user.\"\"\"
                        return 'Hi'

                # now whenever MyException or it's sub-classes are thrown, the
                # user will get `Hi` back
                MyException.register_errorhandler(app)

        Args:
            app (flask.Flask):
                The Flask application to register the standard handler callback
                to.

        Returns:
            fleaker.exceptions.FleakerBaseException:
                Returns the same class this was called on, to provide a fluent
                interface (e.g., register error handlers on multiple apps in
                one method chain).
        """
        app.errorhandler(cls)(cls.errorhandler_callback)

        return app

    def error_page(self):
        """Render the error page we should display in the errorhandler callback
        for this exception.

        This is a method that is used to hook into the standard, automatic
        error handler for Fleaker exceptions. When the error handler runs, and
        is not set to redirect, it will look here for content. If this method
        returns ANYTHING other than ``None``, the returned value will be the
        returned result of the errorhandler. If ``None`` is returned, then the
        errorhandler will not return anything.

        While this provides the content for an error page, the status code for
        your error page is set via the ``status_code`` kwarg passed to the
        Exception's consturctor. Any attempt to return an additional status
        code will not work. The default status code is a 500.

        This is a wonderful location to inject a render of a stock 500
        template. An example of that can be seen here:

        .. code:: python

            import fleaker

            from flask import render_template

            # standard app factory
            def create_app():
                app = fleaker.App.create_app(__name__)

                # now create a base exception for your app
                class BaseException(fleaker.AppException):
                    \"\"\"The base exception for the entire app.\"\"\"

                    def error_page(self):
                        \"\"\"Render our 500 page.\"\"\"
                        return render_template('500.html.jinja')

                # now register the errorhandler for our exception
                BaseException.register_errorhandler(app)

                # and you're done! any unhandled exception thrown that derives
                # from your base exception will return a nice 500 page!

        Returns:
            None|object:
                Returns the response that the entire error handler should also
                return. If the returned response is ``None``, then the error
                handler will ALSO return nothing at all. Any other response
                will be returned through the stack.
        """
        return None


class FleakerException(FleakerBaseException):
    """The base class for all specific exceptions of the Fleaker library
    itself.

    Should NEVER be thrown on it's own unless something has gone horribly
    wrong. Instead, you should define a new Exception that extends this one and
    throw that.
    """


class AppException(FleakerBaseException):
    """The base class for all specific exceptions for an end User implemented
    application.

    Whereas you, as an application developer, should never import and use
    :class:`FleakerException`, :class:`AppException` is fully intended for just
    that use. The ideal usage is to import it as a starter Exception and build
    from there, like so:

    .. code:: python

        from fleaker.exceptions import AppException


        class MyAppException(AppException):
            \"\"\"Base Exception for my app!\"\"\"

        class UnauthorizedUserException(AppException):
            \"\"\"Exception for bad users.\"\"\"

    This gives you all the nice baked in benefits of Fleaker's own base
    Exception, but provides the benefit of a single Exception Hierarchy
    dedicated to your app.

    Excepting :class:`AppException` will NEVER catch :class:`FleakerException`!

    The custom features this base exception provides are:
        1. The ability to specify a status code with your exception.
        2. A small error handler callback method that does the following:
            1. Automatically rollback the database session, unless
               the ``prevent_rollback`` kwarg is ``True``.
            2. Automatically set a flash message of a given level. Message
               comes from the ``flash_message`` kwarg and severity level comes
               from the ``flash_level`` kwarg.
            3. Automatically redirect the client to another route. The route
               should be set via the ``redirect`` kwarg and kwargs for the
               redirect should be set via the ``redirect_args`` kwarg, both are
               passed straight to :func:`flask.url_for`.

    .. admonition:: Always Have Your Own Base Exception!

       Always ensure the first thing you do with the :class:`AppException` is
       to extend it into a new base exception, then extend from there. Doing
       this allows your Fleaker app to play nicely with other Fleaker apps that
       may be running at the same time!

       .. code:: python

          # my_app/exceptions.py
          from fleaker import AppException


          class BaseException(AppException):
              \"\"\"The base exception for my awesome application!\"\"\"

          # never do this:
          # class SpecificException(AppException):
          # always do this:
          class SpecificException(BaseException):
              \"\"\"Thrown when something specific happens!\"\"\"
    """


class ErrorAwareApp(BaseApplication):
    """The :class:`ErrorAwareApp` Application Mixin is a mixin used to
    automatically register a standard errorhandler function for the
    :class:`AppException` exception class. This registration is done
    immediately after App creation.

    If this registration is done, then any instances of :class:`AppException`
    that bubble out of a View will be automatically handled on a best effort
    basis.

    For now, see the thorough documentation around :class:`AppException` and
    :class:`FleakerBaseException` for more info.

    This mixin accepts one custom app creation option:
        * ``register_errohandler`` - a boolean indicating if we want to
          automatically register an errorhandler for the :class:`AppException`
          exception class after we create this App. Pass ``False`` to prevent
          registration. Default is ``True``.

    """
    # @TODO (exc, docs): Provide more context and a mini-tutorial here.

    @classmethod
    def post_create_app(cls, app, **settings):
        """Register the errorhandler for the AppException to the passed in
        App.

        Args:
            app (fleaker.base.BaseApplication): A Flask application that
                extends the Fleaker Base Application, such that the hooks are
                implemented.

        Kwargs:
            register_errorhandler (bool): A boolean indicating if we want to
                automatically register an errorhandler for the
                :class:`AppException` exception class after we create this App.
                Pass ``False`` to prevent registration. Default is ``True``.


        Returns:
            fleaker.base.BaseApplication: Returns the app it was given.
        """
        register_errorhandler = settings.pop('register_errorhandler', True)

        if register_errorhandler:
            AppException.register_errorhandler(app)

        return app
