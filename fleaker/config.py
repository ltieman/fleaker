# ~*~ coding: utf-8 ~*~
"""
fleaker.config
~~~~~~~~~~~~~~

This module implements various utilities for configuring your Fleaker
:class:`App`.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import types

import flask


class MultiStageConfigurableApp(flask.Flask):
    """The :class:`MultiStageConfigurableApp` is a mixin used to provide the
    primary ``configure`` method used to configure a `Fleaker` :class:`App`.
    """

    def configure(self, *args):
        """Configure the Application through a varied number of sources of
        different types.

        This function chains multiple possible configuration methods together
        in order to just "make it work". You can pass multiple configuration
        sources in to the method and each one will be tried in a sane fashion.
        Later sources will override earlier sources if keys collide. For
        example:

        .. code:: python
            from application import default_config
            app.configure(default_config, os.env, '.secrets')

        In the above example, values stored in ``default_config`` will be
        loaded first, then overwritten by those in ``os.env``, and so on.

        An endless number of configuration sources may be passed.

        Configuration sources are type checked and processed according to the
        following rules:

        * ``string`` - if the source is a ``str``, we will assume it is a file
          that should be loaded. If the file ends in ``.json``, then
          :method:`flask.Config.from_json` is used; otherwise,
          :method:`flask.Config.from_pyfile` is used.
        * ``dict`` - if the source is a ``dict``, then
          :method:`flask.Config.from_mapping` will be used.
        * ``class`` or ``module`` - if the source is an uninstantiated
          ``class`` or ``module``, then :method:`flask.Config.from_object` will
          be used.

        @TODO: Handle the stuff with the leading dot, if we end up using that.
        """

        for item in args:
            # @TODO: Bring in a compat library
            if isinstance(item, basestring):
                # @TODO: Support config from json
                self._configure_from_module(item)
            elif isinstance(item, dict):
                self._configure_from_mapping(item)
            elif isinstance(item, (types.ModuleType, type)):
                self._configure_from_object(item)
            else:
                # @TODO: Better error message
                raise TypeError("Could not determine a valid type for this"
                                " configuration object! {}".format(item))

    def _configure_from_module(self, item):
        """
        @TODO: Fill me out
        """
        path = item
        if item[0] == '.':
            path = self.import_name + item

        if not path.endswith('.py'):
            path += '.py'

        self.config.from_pyfile(path)

        return self

    def _configure_from_mapping(self, item):
        """
        @TODO: Fill me out
        """
        self.config.from_mapping(item)

        return self

    def _configure_from_object(self, item):
        """
        @TODO: Fill me out
        """
        self.config.from_object(item)

        return self


class EnvironmentConfigurableApp(flask.Flask):
    """
    @TODO: Flesh me out; but the general idea here is this guy implements
    `configure_from_environment` which does the environment configuration
    setting that GemSafe uses.
    """
