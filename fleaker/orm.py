# ~*~ coding: utf-8 ~*~
"""
fleaker.orm
~~~~~~~~~~~

The Fleaker orm module provides simple hooks and bindings for usage with
popular ORM's.

By choosing to install either ``fleaker[peewee]`` or ``fleaker[sqlalchemy]``
you automatically opt-in to using either of those two ORM's, which Fleaker will
automatically configure for you.

The database proxy provided by Fleaker is always ``fleaker.db`` regardless of
which ORM you are using. This proxy will provide a ``Model`` attribute no
matter what, and you can safely extend off of that.

From there, the differences between the PeeWee and the SQLAlchemy ORM backends
are described in the relevant ``PeeWee`` (insert link here) and
```SQLAlchemy``` (insert link here) sections.

Attributes:
    db (werkzeug.local.LocalProxy): A proxy that will always point to the right
        database. This is what you should import and interact with and allow
        Fleaker to update it to the right value.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

# @TODO Nuke the sqlalchemy bits of this from orbit.

from __future__ import absolute_import

from functools import partial

from werkzeug.local import LocalProxy

from .base import BaseApplication
from .constants import MISSING

try:
    import peewee
    from playhouse import flask_utils
    _PEEWEE_EXT = flask_utils.FlaskDB()
    # @TODO (orm): Figure out how to get rid of this. I would ideally like
    # a dedicated proxy of ``fleaker.orm.Model`` that will dynamically figure
    # out which base class it should pull from at runtime; if that's doable. If
    # not, we'll add larger base models for each and you can just import those,
    # won't be a big deal.
    PeeweeModel = _PEEWEE_EXT.Model
except ImportError:
    peewee = MISSING
    flask_utils = MISSING
    _PEEWEE_EXT = MISSING
    # @TODO (orm): Make this equal to a special util class that evaluates to
    # Falsey like a MISSING, but when called raises an error pointing this out
    # to the user
    PeeweeModel = MISSING

try:
    import sqlalchemy
    import flask_sqlalchemy
    _SQLA_EXT = flask_sqlalchemy.SQLAlchemy()
    # @TODO (orm): Figure out how to get rid of this. I would ideally like
    # a dedicated proxy of ``fleaker.orm.Model`` that will dynamically figure
    # out which base class it should pull from at runtime; if that's doable. If
    # not, we'll add larger base models for each and you can just import those,
    # won't be a big deal.
    SqlalchemyModel = _SQLA_EXT.Model
except ImportError:
    sqlalchemy = MISSING
    flask_sqlalchemy = MISSING
    _SQLA_EXT = MISSING
    # @TODO (orm): Make this equal to a special util class that evaluates to
    # Falsey like a MISSING, but when called raises an error pointing this out
    # to the user
    SqlalchemyModel = MISSING

_PEEWEE_BACKEND = 'peewee'
_SQLALCHEMY_BACKEND = 'sqlalchemy'


def _discover_ideal_backend(orm_backend):
    """Auto-discover the ideal backend based on what is installed.

    Right now, handles discovery of:
      * PeeWee
      * SQLAlchemy

    Args:
        orm_backend (str): The ``orm_backend`` value that was passed to the
            ``create_app`` function. That is, the ORM Backend the User
            indicated they wanted to use.

    Returns:
        str|fleaker.missing.MissingSentinel: Returns a string for the ideal
            backend if it found one, or :obj:`fleaker.MISSING` if we couldn't
            find one.

    Raises:
        RuntimeError: Raised if no user provided ORM Backend is given and BOTH
            PeeWee and SQLAlchemy are installed.
    """
    if orm_backend:
        return orm_backend

    if peewee is not MISSING and sqlalchemy is not MISSING:
        raise RuntimeError('Both PeeWee and SQLAlchemy detected as installed, '
                           'but no explicit backend provided! Please specify '
                           'one!')
    if peewee is not MISSING:
        return _PEEWEE_BACKEND
    elif sqlalchemy is not MISSING:
        return _SQLALCHEMY_BACKEND
    else:
        return MISSING


class ORMAwareApp(BaseApplication):
    """The :class:`ORMAwareApp` is a mixin used to implement automatic ORM
    discovery and instantiation of the SQLAlchemy or PeeWee ORMs. By using it
    in your composed app, whenever you configure your application to be aware
    of a database, this just kicks and finishes the rest!

    For the top level DB proxy you should use for things like model classes,
    please use :attr:`fleaker.orm.db` which will automatically return the proper
    ORM Extension.

    Here's a quick sample:

    .. code:: python

        # main app factory
        def create_app():
            app = fleaker.App(__name__)
            # use a simple SQLite database
            app.configure({
                "DATABASE": "sqlite:///test_db.db"
            })
            # DONE! Now the DB is valid!

        # in base_model.py:
        import peewee

        from fleaker import db

        class BaseModel(db.Model):
            # any other ORM-specific config options you need go here
            pass

        class UserModel(BaseModel):
            name = peewee.CharField()

        UserModel.create_table()  # NOTE: Database migrations are an exercise
                                  # left to the reader!
        my_user = UserModel(name='Tom Hanks')
        my_user.save()

        tom = my_user.select().where(UserModel.name == 'Tom Hanks').get()
        # boom! we've made two models, created a table, and saved a user!

    This mixin supports two custom app creation options:
        * ``orm_backend`` - a string that is either ``'peewee'`` or
          ``'sqlalchemy`` that can be used to tell Fleaker exactly which ORM
          you want.
        * ``peewee_database`` - a string containing a Database Connection URI
          that PeeWee can use to immediately initialize itself. If your app
          does not intend to provide configuration via the ``DATABASE`` config
          value and does not implement the
          :class:`fleaker.config.MultiStageConfigurableApp` then you will need
          this (hint: the standard app DOES implement the
          MultiStageConfigurableApp).

    This mixin has one configuration value of relevance:
        * ``DATABASE`` - this is a string that should contain the Database
          Connection URI we should use to connect to the proper database. It
          will be passed to PeeWee's created extension.
    """
    # @TODO (orm): Clean this module up and try to get rid of globals/ugly names/
    #              hacks. Make it clean, make it pop.
    # @TODO (orm): Finish SQLA implementation.
    # @TODO (orm): Fix how `post_create_app` works. Right now it tries to
    #              INSTANTLY determine the ORM backend upon creation. This is
    #              fine... unless you don't want an ORM and have both SQLA and
    #              PeeWee installed >.< Besides, we shouldn't do this on creation,
    #              but rather when we init the extension. Moving all of the meat
    #              in post_create_app to an post_configure hook should solve most
    #              of this problem and SIGNIFICANTLY clean up the implementation.
    # @TODO (orm): More docs about configuration and differences between SQLA and
    #              PeeWee setup; refer users to the actual docs at the end.

    @classmethod
    def post_create_app(cls, app, **settings):
        """Init the extension for our chosen ORM Backend, if possible.

        This method will ensure that the ``db`` proxy is set to the right
        extension and that that extension is properly created and configured.
        Since it needs to call ``init_app`` it MUST be a Post Create Hook.

        If the chosen backend is PeeWee and no ``DATABASE`` config value is
        provided, we will delay initializing the extension until one is.

        Args:
            app (flask.Flask): The Flask application that was just made through
                the :meth:`create_app` factory that we should bind extensions
                to.

        Kwargs:
            orm_backend (str): If you want to explicitly specify an ORM Backend
                to use, you should send it in this kwarg. Valid values are
                either: ``'peewee'`` or ``'sqlalchemy'``.
            peewee_database (str): An explicit database connection URI we
                should immeditately add to the configuration that should be
                used to configure the PeeWee ORM Backend. This will result in
                the ``DATABASE`` key being set to this value in the config and
                will result in the PeeWee Flask extension being initialized
                IMMEDIATELY and not delayed until the next call to
                :meth:`configure`.

        Returns:
            flask.Flask: Returns the app it was given once this is done.

        Raises:
            RuntimeError: This is raised if we are asked to create the PeeWee
                ORM, but are not given a database URI in either the
                ``DATABASE`` config value, or the explicit ``peewee_database``
                setting.
        """
        global _SELECTED_BACKEND
        backend = settings.pop('orm_backend', None)
        backend = _discover_ideal_backend(backend)

        # did not specify a backend, bail early
        if backend is MISSING:
            return app

        _swap_backends_error = ('Cannot swap ORM backends after one is '
                                'declared!')

        if backend == _PEEWEE_BACKEND:
            if (_SELECTED_BACKEND is not MISSING
                    and _SELECTED_BACKEND != _PEEWEE_EXT):
                raise RuntimeError(_swap_backends_error)

            # @TODO (orm): Does this really need to be ``peewee_database``? can
            # it be ``orm_database``?
            database_uri = settings.pop('peewee_database', None)
            if database_uri:
                app.config['DATABASE'] = database_uri

            if 'DATABASE' not in app.config:
                # since there is no DATABASE in the config, we need to wait
                # until we init this; so we'll just do it after configure is
                # called.
                try:
                    app.add_post_configure_callback(
                        partial(cls._init_peewee_ext, app),
                        run_once=True
                    )
                except NotImplementedError:
                    # this composed app doesn't implement multi-stage
                    # configuration, so there's no way we can proceed without
                    # an explicit DB =/; yes it's possible this could swallow
                    # another error, but if it does... the easiest fix is to do
                    # the same
                    # @TODO (docs): Multi Stage Configuration should be in
                    # the docs
                    err_msg = """\
                    The app you are trying to construct does not support
                    Multi Stage Configuration and no connection info for the
                    database was given at creation! Please call `create_app`
                    again and provide your database connection string as the
                    `peewee_database` kwarg!\
                    """
                    raise RuntimeError(err_msg)
            else:
                # the DATABASE is already present, go ahead and just init now
                cls._init_peewee_ext(app)

            _SELECTED_BACKEND = _PEEWEE_EXT

        elif backend == _SQLALCHEMY_BACKEND:
            # @TODO (orm): Finish SQLA implementation
            # do sqla bootstrap code
            if (_SELECTED_BACKEND is not MISSING
                    and _SELECTED_BACKEND != _SQLA_EXT):
                raise RuntimeError(_swap_backends_error)

            _SELECTED_BACKEND = _SQLA_EXT
            _SQLA_EXT.init_app(app)

        else:
            err_msg = ("Explicit ORM backend provided, but could not recognize"
                       " the value! Valid values are: '{}'  and '{}';"
                       " received: '{}' instead!")
            err_msg = err_msg.format(_PEEWEE_BACKEND, _SQLALCHEMY_BACKEND,
                                     backend)

            raise RuntimeError(err_msg)
        return app

    @classmethod
    def _init_peewee_ext(cls, app, dummy_configuration=None,
                         dummy_configure_args=None):
        """Init the actual PeeWee extension with the app that was created.

        Since PeeWee requires the ``DATABASE`` config parameter to be present
        IMMEDIATELY upon initializing the application, we need to delay this
        construction. This is because, in standard use, we will create the app
        and attempt to init this extension BEFORE we configure the app, which
        is totally fine. To fix this, we just need to set this up to try and
        run after every call to configure. If there is not ``DATABASE`` config
        parameter present when run, this method does nothing other than
        reschedule itself to run in the future.

        In all cases, this is a Post Configure Hook that should RUN ONCE!

        Args:
            app (flask.Flask): The application you want to init the PeeWee
                Flask extension for. Hint: if you need to use this as
                a callback, use a partial to provide this.
            dummy_configuration (dict): The resulting application configuration
                that the post_configure hook provides to all of it's callbacks.
                We will NEVER use this, but since we utilize the post_configure
                system to register this for complicated apps, we gotta accept
                it.
            dummy_configure_args (list[object]): The args passed to the
                :meth:`configure` function that triggered this callback. Just
                like the above arg, we'll never use it, but we must accept it.
        """
        # the database still isn't present, go ahead and register the callback
        # again, so we can try later.
        if 'DATABASE' not in app.config:
            app.add_post_configure_callback(partial(cls._init_peewee_ext, app),
                                            run_once=True)
            return

        _PEEWEE_EXT.init_app(app)


# @TODO: Convert to a stack and do this a bit more properly; right now you only
# get ONE backend PER THREAD, not PER APP.
_SELECTED_BACKEND = MISSING
def _find_db_ext():
    """Find the current ORM Extension this App is using.

    After we discover and initialize the proper ORM Extension we need the
    ``db`` proxy to resolve to it, which is exactly what this method does here.

    Does this by simply inspecting a global, but that could be done better.

    Returns:
        flask_utils.FlaskDB|flask_sqlalchemy.SQLAlchemy: The correct and
            current ORM Extension in use for this App.
    """
    if _SELECTED_BACKEND is MISSING:
        # @TODO: Do like Flask does with the context error and have a single
        # leading line that sort of explains the issue and is easily searched?
        raise RuntimeError("You have attempted to use the Fleaker DB proxy "
                           "before it was initialized! Please ensure you are "
                           "in the right context or push it yourself! Please "
                           "see the documentation for more information!")
    return _SELECTED_BACKEND

db = LocalProxy(_find_db_ext)

# NEVER export this; we're TOTALLY done with it!
del _find_db_ext
