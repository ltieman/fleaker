# ~*~ coding: utf-8 ~*~
"""
fleaker.config
~~~~~~~~~~~~~~

This module implements various utilities for configuring your Fleaker
:class:`App`.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import copy
import importlib
import os
import types

from os.path import splitext

from werkzeug.datastructures import ImmutableDict

from ._compat import string_types
from .base import BaseApplication


class MultiStageConfigurableApp(BaseApplication):
    """The :class:`MultiStageConfigurableApp` is a mixin used to provide the
    primary :meth:`configure` method used to configure a ``Fleaker``
    :class:`~fleaker.App`.

    .. versionadded:: 0.1.0
       The :class:`MultiStageConfigurableApp` class has existed since Fleaker
       was conceived.
    """

    def __init__(self, import_name, **settings):
        """Construct the app.

        Adds a list for storing our post configure callbacks.

        All args and kwargs are the same as the
        :class:`fleaker.base.BaseApplication`.
        """
        # A dict of all callbacks we should run after configure finishes. These
        # are then separated by those that should run once, or run multiple
        # times
        # @TODO (QoL): There has to be a cleaner way to do this, do that
        self._post_configure_callbacks = {
            'multiple': [],
            'single': [],
        }

        super(MultiStageConfigurableApp, self).__init__(import_name,
                                                        **settings)

    def configure(self, *args, **kwargs):
        """Configure the Application through a varied number of sources of
        different types.

        This function chains multiple possible configuration methods together
        in order to just "make it work". You can pass multiple configuration
        sources in to the method and each one will be tried in a sane fashion.
        Later sources will override earlier sources if keys collide. For
        example:

        .. code:: python

            from application import default_config
            app.configure(default_config, os.environ, '.secrets')

        In the above example, values stored in ``default_config`` will be
        loaded first, then overwritten by those in ``os.environ``, and so on.

        An endless number of configuration sources may be passed.

        Configuration sources are type checked and processed according to the
        following rules:

        * ``string`` - if the source is a ``str``, we will assume it is a file
          or module that should be loaded. If the file ends in ``.json``, then
          :meth:`flask.Config.from_json` is used; if the file ends in ``.py``
          or ``.cfg``, then :meth:`flask.Config.from_pyfile` is used; if the
          module has any other extension we assume it is an import path, import
          the module and pass that to :meth:`flask.Config.from_object`. See
          below for a few more semantics on module loading.
        * ``dict-like`` - if the source is ``dict-like``, then
          :meth:`flask.Config.from_mapping` will be used. ``dict-like`` is
          defined as anything implementing an ``items`` method that returns
          a tuple of ``key``, ``val``.
        * ``class`` or ``module`` - if the source is an uninstantiated
          ``class`` or ``module``, then :meth:`flask.Config.from_object` will
          be used.

        Just like Flask's standard configuration, only uppercased keys will be
        loaded into the config.

        If the item we are passed is a ``string`` and it is determined to be
        a possible Python module, then a leading ``.`` is relevant. If
        a leading ``.`` is provided, we assume that the module to import is
        located in the current package and operate as such; if it begins with
        anything else we assume the import path provided is absolute. This
        allows you to source configuration stored in a module in your package,
        or in another package.

        Args:
            *args (object):
                Any object you want us to try to configure from.

        Keyword Args:
            whitelist_keys_from_mappings (bool):
                Should we whitelist the keys we pull from mappings? Very useful
                if you're passing in an entire OS ``environ`` and you want to
                omit things like ``LESSPIPE``. If no whitelist is provided, we
                use the pre-existing config keys as a whitelist.
            whitelist (list[str]):
                An explicit list of keys that should be allowed. If provided
                and ``whitelist_keys`` is ``True``, we will use that as our
                whitelist instead of pre-existing app config keys.
        """
        whitelist_keys_from_mappings = kwargs.get(
            'whitelist_keys_from_mappings', False
        )
        whitelist = kwargs.get('whitelist')

        for item in args:
            if isinstance(item, string_types):
                _, ext = splitext(item)

                if ext == '.json':
                    self._configure_from_json(item)
                elif ext in ('.cfg', '.py'):
                    self._configure_from_pyfile(item)
                else:
                    self._configure_from_module(item)

            elif isinstance(item, (types.ModuleType, type)):
                self._configure_from_object(item)

            elif hasattr(item, 'items'):
                # assume everything else is a mapping like object; ``.items()``
                # is what Flask uses under the hood for this method
                # @TODO: This doesn't handle the edge case of using a tuple of
                # two element tuples to config; but Flask does that. IMO, if
                # you do that, you're a monster.
                self._configure_from_mapping(
                    item,
                    whitelist_keys=whitelist_keys_from_mappings,
                    whitelist=whitelist
                )

            else:
                raise TypeError("Could not determine a valid type for this"
                                " configuration object: `{}`!".format(item))

        # we just finished here, run the post configure callbacks
        self._run_post_configure_callbacks(args)

    def _configure_from_json(self, item):
        """Load configuration from a JSON file.

        This method will essentially just ``json.load`` the file, grab the
        resulting object and pass that to ``_configure_from_object``.

        Args:
            items (str):
                The path to the JSON file to load.

        Returns:
            fleaker.App:
                Returns itself.
        """
        self.config.from_json(item)

        return self

    def _configure_from_pyfile(self, item):
        """Load configuration from a Python file. Python files include Python
        source files (``.py``) and ConfigParser files (``.cfg``).

        This behaves as if the file was imported and passed to
        ``_configure_from_object``.

        Args:
            items (str):
                The path to the Python file to load.

        Returns:
            fleaker.App:
                Returns itself.
        """
        self.config.from_pyfile(item)

        return self

    def _configure_from_module(self, item):
        """Configure from a module by import path.

        Effectively, you give this an absolute or relative import path, it will
        import it, and then pass the resulting object to
        ``_configure_from_object``.

        Args:
            item (str):
                A string pointing to a valid import path.

        Returns:
            fleaker.App:
                Returns itself.
        """
        package = None
        if item[0] == '.':
            package = self.import_name

        obj = importlib.import_module(item, package=package)

        self.config.from_object(obj)

        return self

    def _configure_from_mapping(self, item, whitelist_keys=False,
                                whitelist=None):
        """Configure from a mapping, or dict, like object.

        Args:
            item (dict):
                A dict-like object that we can pluck values from.

        Keyword Args:
            whitelist_keys (bool):
                Should we whitelist the keys before adding them to the
                configuration? If no whitelist is provided, we use the
                pre-existing config keys as a whitelist.
            whitelist (list[str]):
                An explicit list of keys that should be allowed. If provided
                and ``whitelist_keys`` is true, we will use that as our
                whitelist instead of pre-existing app config keys.

        Returns:
            fleaker.App:
                Returns itself.
        """
        if whitelist is None:
            whitelist = self.config.keys()

        if whitelist_keys:
            item = {k: v for k, v in item.items() if k in whitelist}

        self.config.from_mapping(item)

        return self

    def _configure_from_object(self, item):
        """Configure from any Python object based on it's attributes.

        Args:
            item (object):
                Any other Python object that has attributes.

        Returns:
            fleaker.App:
                Returns itself.
        """
        self.config.from_object(item)

        return self

    def configure_from_environment(self, whitelist_keys=False, whitelist=None):
        """Configure from the entire set of available environment variables.

        This is really a shorthand for grabbing ``os.environ`` and passing to
        :meth:`_configure_from_mapping`.

        As always, only uppercase keys are loaded.

        Keyword Args:
            whitelist_keys (bool):
                Should we whitelist the keys by only pulling those that are
                already present in the config? Useful for avoiding adding
                things like ``LESSPIPE`` to your app config. If no whitelist is
                provided, we use the current config keys as our whitelist.
            whitelist (list[str]):
                An explicit list of keys that should be allowed. If provided
                and ``whitelist_keys`` is true, we will use that as our
                whitelist instead of pre-existing app config keys.

        Returns:
            fleaker.base.BaseApplication:
                Returns itself.
        """
        self._configure_from_mapping(os.environ, whitelist_keys=whitelist_keys,
                                     whitelist=whitelist)

        return self

    def add_post_configure_callback(self, callback, run_once=False):
        """Add a new callback to be run after every call to :meth:`configure`.

        Functions run at the end of :meth:`configure` are given the
        application's resulting configuration and the arguments passed to
        :meth:`configure`, in that order. As a note, this first argument will
        be an immutable dictionary.

        The return value of all registered callbacks is entirely ignored.

        Callbacks are run in the order they are registered, but you should
        never depend on another callback.

        .. admonition:: The "Resulting" Configuration

            The first argument to the callback is always the "resulting"
            configuration from the call to :meth:`configure`. What this means
            is you will get the Application's FROZEN configuration after the
            call to :meth:`configure` finished. Moreover, this resulting
            configuration will be an
            :class:`~werkzeug.datastructures.ImmutableDict`.

            The purpose of a Post Configure callback is not to futher alter the
            configuration, but rather to do lazy initialization for anything
            that absolutely requires the configuration, so any attempt to alter
            the configuration of the app has been made intentionally difficult!

        Args:
            callback (function):
                The function you wish to run after :meth:`configure`. Will
                receive the application's current configuration as the first
                arugment, and the same arguments passed to :meth:`configure` as
                the second.

        Keyword Args:
            run_once (bool):
                Should this callback run every time configure is called? Or
                just once and be deregistered? Pass ``True`` to only run it
                once.

        Returns:
            fleaker.base.BaseApplication:
                Returns itself for a fluent interface.
        """
        if run_once:
            self._post_configure_callbacks['single'].append(callback)
        else:
            self._post_configure_callbacks['multiple'].append(callback)

        return self

    def _run_post_configure_callbacks(self, configure_args):
        """Run all post configure callbacks we have stored.

        Functions are passed the configuration that resulted from the call to
        :meth:`configure` as the first argument, in an immutable form; and are
        given the arguments passed to :meth:`configure` for the second
        argument.

        Returns from callbacks are ignored in all fashion.

        Args:
            configure_args (list[object]):
                The full list of arguments passed to :meth:`configure`.

        Returns:
            None:
                Does not return anything.
        """
        resulting_configuration = ImmutableDict(self.config)

        # copy callbacks in case people edit them while running
        multiple_callbacks = copy.copy(
            self._post_configure_callbacks['multiple']
        )
        single_callbacks = copy.copy(self._post_configure_callbacks['single'])
        # clear out the singles
        self._post_configure_callbacks['single'] = []

        for callback in multiple_callbacks:
            callback(resulting_configuration, configure_args)

        # now do the single run callbacks
        for callback in single_callbacks:
            callback(resulting_configuration, configure_args)
