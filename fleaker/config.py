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
        """
        @TODO: Fill me out
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
