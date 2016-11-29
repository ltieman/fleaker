# ~*~ coding: utf-8 ~*~
"""
fleaker.exceptions
~~~~~~~~~~~~~~~~~~

Provides test for the common configuration options.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from flask import flash, url_for, redirect

from fleaker import DEFAULT_DICT, MISSING


class _FleakerBaseException(Exception):
    """Base class for all Fleaker Exception Base Classes.

    This Exception should NEVER be used under ANY circumstances. It has two
    uses:
        1. As the parent class for :class:`FleakerException`.
        2. As the parent class for :class:`AppException`.
    Both of those have been done at the time of this writing.

    Now, for an explanation. Fleaker implements two base exceptions. The first
    is :class:`FleakerException` which is the base class for all Exceptions
    that Fleaker itself will throw. It is safe to ``except`` anytime you expect
    Fleaker to possibly fail. The second is :class:`AppException` which is an
    exception that an Application Developer is expected to import and reuse as
    their own Application's base exception.

    We surface the :class:`_FleakerBaseException` to the end user as
    :class:`AppException` because many of the features in
    :class:`_FleakerBaseException` are intended for them to use, such as
    auto-redirects, auto-flash messages, etc. This gives them a very powerful
    base Exception to start building off of. We then reuse this same Exception
    base for :class:`FleakerException` because... why not? Even if Fleaker
    itself won't use most of this, providing the funtionality adds little harm
    and gives us room to grow.

    From there we create two separate Exception hierarchies so that ``except``s
    are always clean and never collide, e.g., you can ``except
    FleakerException`` and NOT implicitly catch all :class:`AppException`s with
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
               passed straight to :meth:`flask.url_for`.

    Attributes:
        message (str): A message for this specific Exception instance. Can be
            passed as either the first arg, or the ``message`` kwarg.
        status_code (int): The status code that processing of this Exception
            should result in. For example, if this exception indicates an
            Authorization Failure, a 403 is a nice status code to use.
        redirect (unicode): If this is set when initializing the exception, it
            must be the name of a route registered to the application. When
            this hits the global error handler for the exception, it can
            optionally redirect the user to this route.
        redirect_args (dict): This dict of args will be piped directly into
            `url_for` for the redirect.
        prevent_rollback (bool): By default, if this exception bubbles up to a
            error handler, the DB transaction will be rolled back. If this
            behavior isn't desirable, set this to false when raising the
            exception.
        flash_message (bool): If the User is being redirected, should the
            exception message be `flash`d to the user? By default, this is
            false.
        flash_level (unicode): If a message is being flashed, what level should
            it be? This value should be one that works with `flask.flash`'s
            second argument.
    """

    redirect = MISSING
    redirect_args = DEFAULT_DICT
    prevent_rollback = False
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

        Args:
            exc (_FleakerBaseException): The exception that was thrown that we
                are to handle.
        """
        # @TODO: Implement this when the ORM/DB stuff is done
        # if not exc.prevent_rollback:
        #     db.session.rollback()

        if exc.flash_message:
            flash(exc.flash_message, exc.flash_level)

        if exc.redirect is not MISSING:
            return redirect(url_for(exc.redirect, **exc.redirect_args))

        # @TODO: Remove this; replace with some real shit
        # return ""


class FleakerException(_FleakerBaseException):
    """The base class for all specific exceptions of the Fleaker library
    itself.

    Should NEVER be thrown on it's own unless something has gone horribly
    wrong. Instead, you should define a new Exception that extends this one and
    throw that.
    """


class AppException(_FleakerBaseException):
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
               passed straight to :meth:`flask.url_for`.
    """
