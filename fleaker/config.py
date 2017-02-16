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
from .constants import MISSING
from .exceptions import ConfigurationError


class MultiStageConfigurableApp(BaseApplication):
    """The :class:`MultiStageConfigurableApp` is a mixin used to provide the
    primary :meth:`configure` method used to configure a ``Fleaker``
    :class:`~fleaker.App`.

    .. versionadded:: 0.1.0
       The :class:`MultiStageConfigurableApp` class has existed since Fleaker
       was conceived.
    """
    # used whenever we find a config file with a bad permission
    permissions_error = ("Found configuration item '{}' at {} but could not "
                         "load it! Are the permissions properly configured?")
    missing_error = ("Could not find configuration item '{}'! Searched path: "
                     "{}.")

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
            ignore_missing (bool):
                Whether or not we should raise an error if a configuration file
                is missing when we go to search for it. If strings are provided
                as your configurable, they are assumed to be file paths. If
                this is ``False`` (the default) and there is no file at that
                path, a :class:`~fleaker.exceptions.ConfigurationError` will be
                raised. If this is ``True``, then no error will be raised and
                we will silently skip that configurable.
        """
        original_opts = {
            'whitelist_keys_from_mappings': kwargs.get(
                'whitelist_keys_from_mappings', False),
            'whitelist': kwargs.get('whitelist'),
            'ignore_missing': kwargs.get('ignore_missing', False),
        }

        for item in args:
            try:
                opts = item.update_options(original_opts, copy=True)
                item = item.get_configurable()
            except AttributeError:
                opts = original_opts.copy()

            if isinstance(item, string_types):
                _, ext = splitext(item)

                if ext == '.json':
                    self._configure_from_json(item, **opts)
                elif ext in ('.cfg', '.py'):
                    self._configure_from_pyfile(item, **opts)
                else:
                    self._configure_from_module(item, **opts)

            elif isinstance(item, (types.ModuleType, type)):
                self._configure_from_object(item, **opts)

            elif hasattr(item, 'items'):
                # assume everything else is a mapping like object; ``.items()``
                # is what Flask uses under the hood for this method
                # @TODO: This doesn't handle the edge case of using a tuple of
                # two element tuples to config; but Flask does that. IMO, if
                # you do that, you're a monster.
                self._configure_from_mapping(item, **opts)

            else:
                raise TypeError("Could not determine a valid type for this"
                                " configuration object: `{}`!".format(item))

        # we just finished here, run the post configure callbacks
        self._run_post_configure_callbacks(args)

    def _configure_from_json(self, item, **kwargs):
        """Load configuration from a JSON file.

        This method will essentially just ``json.load`` the file, grab the
        resulting object and pass that to ``_configure_from_object``.

        Args:
            items (str):
                The path to the JSON file to load.

        Kwargs:
            ignore_missing (bool):
                Should we throw an exception if we cannot locate the requested
                JSON file? Default is False, to throw an exception.

        Returns:
            fleaker.App:
                Returns itself.
        """
        return self._configure_from_file('from_json', item, **kwargs)

    def _configure_from_pyfile(self, item, **kwargs):
        """Load configuration from a Python file. Python files include Python
        source files (``.py``) and ConfigParser files (``.cfg``).

        This behaves as if the file was imported and passed to
        ``_configure_from_object``.

        Args:
            items (str):
                The path to the Python file to load.

        Kwargs:
            ignore_missing (bool):
                Should we throw an exception if we cannot locate the requested
                JSON file? Default is False, to throw an exception.

        Returns:
            fleaker.App:
                Returns itself.
        """
        return self._configure_from_file('from_pyfile', item, **kwargs)

    def _configure_from_file(self, method, item, **kwargs):
        """Wrapper method to call one of Flask's file ``config_from`` methods.

        This is a small wrapper that encapsulates the common error handling we
        do for Flask's file based ``config_from`` methods (currently
        :meth:`~flask.Config.from_pyfile` and :meth:`~flask.Config.from_json`).
        Since the only difference our own :meth:`_configure_from_pyfile` and
        :meth:`_configure_from_json` methods have is which Flask method they
        call, we can encapsulate the rest easily.

        Args:
            method (str):
                The method on :class:`flask.Config` that should be called to
                complete this configuration.
            item (str):
                The sole argument that should be passed to the method
                associated with ``method``. Nominally, this is the path to
                a file.

        Kwargs:
            ignore_missing (bool):
                Should we throw an exception if we cannot locate the requested
                JSON file? Default is False, to throw an exception.

        Raises:
            fleaker.exceptions.ConfigurationError:
                Raised if we cannot find or open the file we need to configure
                from.

        Returns:
            fleaker.App:
                Returns itself.
        """
        config_from = getattr(self.config, method)

        # we always pass in `silent=True`, because we have our own exceptions
        # for this
        try:
            result = config_from(item, silent=True)
        except IOError:
            # file exists, but permissions are wrong
            full_path = os.path.join(self.root_path, item)
            if os.path.exists(full_path):
                raise ConfigurationError(
                    self.permissions_error.format(item, full_path)
                )

            # reraise in this case; if the file is missing we shouldn't hit
            # this branch, so the OS is being whacky
            raise

        # since ``silent=True`` is passed to the underlying Flask method,
        # a False return means we couldn't find what we needed
        if not result and not kwargs.get('ignore_missing'):
            full_path = os.path.join(self.root_path, item)
            raise ConfigurationError(self.missing_error.format(item,
                                                               full_path))

        return self

    def _configure_from_module(self, item, **kwargs):
        """Configure from a module by import path.

        Effectively, you give this an absolute or relative import path, it will
        import it, and then pass the resulting object to
        ``_configure_from_object``.

        Args:
            item (str):
                A string pointing to a valid import path.

        Kwargs:
            ignore_missing (bool):
                Should we throw an exception if we cannot locate the requested
                JSON file? Default is False, to throw an exception.

        Returns:
            fleaker.App:
                Returns itself.
        """
        package = None
        if item[0] == '.':
            package = self.import_name

        try:
            obj = importlib.import_module(item, package=package)
        except ImportError as exc:
            # let's see if this was a permissions error, or a missing module;
            # either way, we need the full path to the python file
            pkg = ''
            if package:
                pkg = importlib.import_module(package)
                pkg = os.path.dirname(pkg.__file__)

            path = item[1:] if item.startswith('.') else item
            path = path.replace('.', os.path.sep) + '.py'
            full_path = os.path.join(pkg, path)

            if os.path.exists(full_path):
                # was a permissions error, give a helpful message
                raise ConfigurationError(
                    self.permissions_error.format(item, full_path)
                )
            elif not kwargs.get('ignore_missing'):
                # resource doesn't exist, raise a different error
                raise ConfigurationError(
                    self.missing_error.format(item, full_path)
                )
        else:
            self.config.from_object(obj)

        return self

    def _configure_from_mapping(self, item, **kwargs):
        """Configure from a mapping, or dict, like object.

        Args:
            item (dict):
                A dict-like object that we can pluck values from.

        Kwargs:
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
        whitelist = kwargs.get('whitelist', False)
        whitelist_keys = kwargs.get('whitelist_keys')

        if whitelist is None:
            whitelist = self.config.keys()

        if whitelist_keys:
            item = {k: v for k, v in item.items() if k in whitelist}

        self.config.from_mapping(item)

        return self

    def _configure_from_object(self, item, **kwargs):
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


class ConfigOption(object):
    # @TODO: Finish the doc
    """:class:`ConfigOption` """

    def __init__(self, configurable, whitelist_keys_from_mappings=MISSING,
                 whitelist=MISSING, ignore_missing=MISSING):
        # @TODO: Finish the doc
        """
        Args:
            configurable (object):
                An item we should attempt to configure from. Item refers to
                a string, object, dictionary, etc.

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
            ignore_missing (bool):
                Whether or not we should raise an error if a configuration file
                is missing when we go to search for it. If strings are provided
                as your configurable, they are assumed to be file paths. If
                this is ``False`` (the default) and there is no file at that
                path, a :class:`~fleaker.exceptions.ConfigurationError` will be
                raised. If this is ``True``, then no error will be raised and
                we will silently skip that configurable.
        """
        self.whitelist_keys_from_mappings = whitelist_keys_from_mappings
        self.whitelist = whitelist
        self.ignore_missing = ignore_missing

        self.configurable = configurable

    def update_options(self, options, copy=False):
        """Update a set of configuration options based on current state.

        If you wish to implement your own :class:`ConfigOption`, or override
        the existing configuratiobn parsing, this is one of the methods you
        should reimplement, alongside :meth:`get_configurable`. This is the
        method that you should then use to hook into any sort of custom option
        parsing you may have.

        Sample usage:

        >>> opts = {}
        >>> config_option = ConfigOption(ignore_missing=True)
        >>> config_option.update_options(opts)
        {'ignore_missing': True, 'whitelist_keys_from_mappings': False, 'whitelist': None}

        Args:
            options (dict);
                The original set of configuration options that we should
                update. Basically, a set of defaults.

        Kwargs:
            copy (bool):
                Should we copy the original options before we update? If
                ``True`` is passed, we will, leaving the originals untouched.
                If ``False`` is passed (the default), we will update in place.

        Returns:
            dict:
                Returns the newly updated dictionary of options.
        """
        if copy:
            options = options.copy()

        if self.whitelist_keys_from_mappings is not MISSING:
            options['whitelist_keys_from_mappings'] = self.whitelist_keys_from_mappings

        if self.whitelist is not MISSING:
            options['whitelist'] = self.whitelist

        if self.ignore_missing is not MISSING:
            options['ignore_missing'] = self.ignore_missing

        return options

    def get_configurable(self):
        """Return the actual configuration item that this class has wrapped.

        If you wish to implement your own :class:`ConfigOption`, or override
        the existing configuratiobn parsing, this is one of the methods you
        should reimplement, alongside :meth:`update_options`. This is the
        method you should use to alter or change a configurable at runtime, if
        desired.

        Returns:
            object:
                The item we should attempt to configure from. Item refers to
                a string, object, dictionary, etc.
        """
        return self.configurable
