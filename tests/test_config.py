# ~*~ coding: utf-8 ~*~
"""
tests.test_config
~~~~~~~~~~~~~~~~~

Provides test for the common configuration options.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import os

import pytest

from werkzeug.datastructures import ImmutableDict

import fleaker

from fleaker.config import ConfigOption, MultiStageConfigurableApp
from fleaker.exceptions import ConfigurationError, FleakerException

import tests.configs.settings as settings

from tests._compat import mock


# a list of non-existent configuration files of all configuration file types,
# useful for tests that test behavior for missing files
MISSING_CONFIGS = [
    './configs/dne.json',
    './configs/dne.py',
    './configs/dne.cfg',
    '/terrible/path/in/general.json',
]

MISSING_MODULES = [
    '.configs.dne',
]

# configuration files with bad permissions (000)
BAD_PERMISSION_CONFIGS = [
    './configs/locked.json',
    './configs/locked.py',
    './configs/locked.cfg',
]

# modules with bad permissions (000), needs a different mocking structure
BAD_PERMISSION_MODULES = [
    '.configs.locked',
]



def _create_app():
    """Utility function to create the app for config testing.

    It requires a bit more work than standard test app creation (but not much).

    Returns:
        fleaker.App: The standard App we just created.
    """
    return fleaker.App('tests')


# @TODO: ALL of these tests should have their names prefixed with config_, like
# so: test_config_basic_configure;
# @TODO: Document the above rule.
def test_basic_configure():
    """Ensure generic configure method works."""
    # since this app is defined in a module, not a package, don't use
    # ``__name__``; ``tests`` is effectively our name.
    app = _create_app()
    app.configure('.configs.settings', '.configs.overrides')

    assert app.config['CANARY']
    assert app.config['SECRET_KEY'] == 'bar'
    assert app.config['THIRD_OPTION'] == 'three'
    assert app.config['TEST_KEY'] == 'foo'


@pytest.mark.environ(FLEAKER_CONFIG_LOADED_FROM_ENV=True)
def test_configure_advanced():
    """Ensure this one method properly configures based on the entire
    environment.
    """
    # @TODO: Finish more configure tests. Add some for more esoteric
    # configuration methods and test the configuration methods directly
    # how do I want configuration to work? just scaffold that shiznit out...

    # since this app is defined in a module, not a package, don't use
    # ``__name__``; ``tests`` is effectively our name.
    app = _create_app()

    # add something to the environ to test for
    # os.environ['FLEAKER_CONFIG_LOADED_FROM_ENV'] = 'True'

    app.configure(
        settings,  # is imported directly and should work
        '.configs.overrides',  # relative path for importing
        'fleaker_config.configs.settings',  # absolute path for settings from
                                            # another module
        './configs/config.json',  # should load a JSON file
        os.environ,  # dict-like, should work as is
        './configs/config.py',  # should load the python file and work
        './configs/config.cfg',  # should load the config file and work
    )
    # I think this is good; now create stubs for all of this and go

    assert app.config['FLEAKER_LOADED_TEST_SETTINGS']
    assert app.config['FLEAKER_LOADED_TEST_OVERRIDES']
    assert app.config['FLEAKER_CONFIG_LOADED']
    assert app.config['FLEAKER_JSON_CONFIG_LOADED']
    assert app.config['FLEAKER_CONFIG_PY_LOADED']
    assert app.config['FLEAKER_CONFIG_CFG_LOADED']
    assert app.config['FLEAKER_CONFIG_LOADED_FROM_ENV'] == 'True'


def test_configure_with_whitelist_keys():
    """Ensure that the ``whitelist_keys`` kwarg works in ``configure``."""
    app = _create_app()

    configs = {
        'FLEAKER_SHOULD_NOT_BE_PRESENT': True,
        'CANARY': 'Loaded from mapping'
    }

    app.configure('.configs.settings', configs,
                  whitelist_keys_from_mappings=True)

    assert 'FLEAKER_SHOULD_NOT_BE_PRESENT' not in app.config
    assert app.config['CANARY'] == 'Loaded from mapping'

    # now test an explicit whitelist
    app = _create_app()

    configs['FLEAKER_SHOULD_BE_PRESENT'] = True

    app.configure('.configs.settings', configs,
                  whitelist_keys_from_mappings=True,
                  whitelist=('FLEAKER_SHOULD_BE_PRESENT',))

    assert 'FLEAKER_SHOULD_NOT_BE_PRESENT' not in app.config
    # CANARY's value shouldn't be updated
    assert app.config['CANARY'] == True
    assert app.config['FLEAKER_SHOULD_BE_PRESENT']


@pytest.mark.environ(FLEAKER_CONFIG_LOADED_FROM_ENV=True)
def test_configure_from_environment():
    """Ensure that we can quickly configure from the environment."""
    app = _create_app()
    app.configure_from_environment()

    assert app.config['FLEAKER_CONFIG_LOADED_FROM_ENV'] == 'True'


@pytest.mark.environ(FLEAKER_SHOULD_NOT_BE_PRESENT=True,
                     CANARY='Loaded from env')
def test_configure_from_environment_whitelist():
    """Ensure configuring from the env with a whitelist works."""
    app = _create_app()

    app.configure('.configs.settings')
    app.configure_from_environment(whitelist_keys=True)

    assert 'FLEAKER_SHOULD_NOT_BE_PRESENT' not in app.config
    # CANARY is loaded from the standard ``configs.settings`` so it passes the
    # whitelist
    assert app.config['CANARY'] == 'Loaded from env'


@pytest.mark.environ(FLEAKER_SHOULD_NOT_BE_PRESENT=True,
                     CANARY='Loaded from env',
                     FLEAKER_SHOULD_BE_PRESENT=True)
def test_configure_from_environment_explicit_whitelist():
    """Ensure configure from env with a provided whitelist works."""
    app = _create_app()

    app.configure('.configs.settings')
    app.configure_from_environment(whitelist_keys=True,
                                   whitelist=('FLEAKER_SHOULD_BE_PRESENT',))

    assert 'FLEAKER_SHOULD_NOT_BE_PRESENT' not in app.config
    # CANARY's value shouldn't be updated
    assert app.config['CANARY'] == True
    assert app.config['FLEAKER_SHOULD_BE_PRESENT'] == 'True'


def test_configure_from_mapping_whitelist():
    """Ensure configuring from only a mapping with a whitelist works."""
    app = _create_app()

    whitelist = ('FLEAKER_SHOULD_BE_PRESENT',)
    configs = {
        'FLEAKER_SHOULD_NOT_BE_PRESENT': True,
        'FLEAKER_SHOULD_BE_PRESENT': True,
    }

    app.configure(configs, whitelist_keys_from_mappings=True,
                  whitelist=whitelist)

    assert app.config['FLEAKER_SHOULD_BE_PRESENT'] == True
    assert 'FLEAKER_SHOULD_NOT_BE_PRESENT' not in app.config


def test_config_post_configure_callbacks():
    """Ensure post configure callbacks work."""
    app = MultiStageConfigurableApp.create_app('tests')
    app.config['CANARY'] = True

    configure_args = {
        'FOO': 'bar',
    }

    def evil_cb(cfg, cfg_args):
        """This fella tries to change the config so we can make sure we pass
        around a frozen config.
        """
        # this is the only way you can change the config from here
        app.config['BAD_VAL'] = True

    def small_cb(cfg, cfg_args):
        """Ensure that we get the right arguments to our callbacks."""
        assert cfg['CANARY']
        assert cfg['FOO'] == 'bar'
        assert cfg_args == (configure_args,)
        assert 'BAD_VAL' not in cfg

    # we need the proper arguments to the call assertions below, so construct
    # them.
    expected_config = app.config.copy()
    expected_config['FOO'] = 'bar'
    expected_config = ImmutableDict(expected_config)

    # make sure we can count calls and call order
    small_cb = mock.MagicMock(wraps=small_cb)
    evil_cb = mock.MagicMock(wraps=evil_cb)
    parent_mock = mock.Mock()
    parent_mock.m1, parent_mock.m2 = small_cb, evil_cb

    assert not app._post_configure_callbacks['single']
    assert not app._post_configure_callbacks['multiple']

    app.add_post_configure_callback(evil_cb)
    app.add_post_configure_callback(small_cb)

    assert len(app._post_configure_callbacks) == 2

    app.configure(configure_args)

    # ensure we called the right number of times in the right order
    assert small_cb.call_count == 1
    assert evil_cb.call_count == 1
    parent_mock.assert_has_calls([
        mock.call.m2(expected_config, (configure_args,)),
        mock.call.m1(expected_config, (configure_args,)),
    ])


@pytest.mark.parametrize("run_once", [True, False])
@pytest.mark.timeout(0.5)  # this is what will make the test pass or fail
def test_config_post_configure_reschedules(run_once):
    """Ensure that adding callbacks while running a callback doesn't infinite
    loop us.
    """
    app = _create_app()

    def self_scheduling_cb(dummy_config, dummy_args):
        """Schedules himself to ensure infinite loops can't happen."""
        app.add_post_configure_callback(self_scheduling_cb, run_once=run_once)

    app.add_post_configure_callback(self_scheduling_cb, run_once=run_once)

    app.configure({
        'FOO': 'bar',
    })


@pytest.mark.parametrize("run_once", [True, False])
def test_config_post_configure_add_run_once(run_once):
    """Ensure we can add a `run_once` callback when running others."""
    app = _create_app()

    def run_once_cb(dummy_cfg, dummy_args):
        """This will be run once, but we want to make sure we can schedule it
        while running other callbacks.
        """

    def initial(dummy_cfg, dummy_args):
        """This will be the first to run and will schedule the other."""
        app.add_post_configure_callback(run_once_cb, run_once=True)

    run_once_cb = mock.MagicMock(wraps=run_once_cb)
    initial = mock.MagicMock(wraps=initial)

    app.add_post_configure_callback(initial, run_once=run_once)

    app.configure({
        "FOO": "bar",
    })

    assert len(app._post_configure_callbacks['single']) == 1
    # initial should have run, but not the run_once
    assert initial.call_count == 1
    assert run_once_cb.call_count == 0

    app.configure({"BAR": "baz"})

    # and now run once should have run
    assert run_once_cb.call_count == 1


def test_config_post_configure_run_multiple():
    """Ensure callbacks run once when indicated."""
    app = _create_app()

    def runs_once(dummy_cfg, dummy_args):
        """Runs only once."""

    def runs_every_time(dummy_cfg, dummy_args):
        """Runs on each call."""

    runs_once = mock.MagicMock(wraps=runs_once)
    runs_every_time = mock.MagicMock(wraps=runs_every_time)

    app.add_post_configure_callback(runs_once, run_once=True)
    app.add_post_configure_callback(runs_every_time)

    app.configure({
        'FOO': 'bar',
    })

    assert runs_once.call_count == 1
    assert runs_every_time.call_count == 1

    app.configure({
        'FOO': 'bar',
    })

    assert runs_once.call_count == 1
    assert runs_every_time.call_count == 2


@pytest.mark.parametrize("config_file", MISSING_CONFIGS)
def test_config_configure_ignore_missing(config_file):
    """Ensure that ignore_missing doesn't fail for missing files/modules."""
    app = _create_app()

    # ensure that a missing module doesn't break anything
    app.configure(config_file, '.configs.config', ignore_missing=True)

    assert app.config['FLEAKER_CONFIG_PY_LOADED']
    assert app.config['THIRD_OPTION'] == 'from config.py'


@pytest.mark.parametrize("config_file", MISSING_CONFIGS)
def test_config_config_option_ignore_missing(config_file):
    """Ensure ConfigOption works with ignore_missing."""
    app = _create_app()

    opt = ConfigOption(config_file, ignore_missing=True)

    app.configure(opt, '.configs.config')

    assert app.config['FLEAKER_CONFIG_PY_LOADED']
    assert app.config['THIRD_OPTION'] == 'from config.py'


def test_config_config_option_does_not_override_configure():
    """Ensure that if a ConfigOption has no value, it won't override configure
    args.
    """
    app = _create_app()

    opt = ConfigOption('.configs.config')

    app.configure(opt, whitelist=['THIRD_OPTION'],
                  whitelist_keys_from_mappings=True)

    # since a `whitelist` is passed in the call to configure, it should still
    # be used even though `ConfigOption` doesn't have one
    assert 'FLEAKER_CONFIG_PY_LOADED' not in app.config
    assert app.config['THIRD_OPTION'] == 'from config.py'


def test_config_config_option_share_settings():
    """Ensure that arguments from `configure` work with ConfigOption."""
    app = _create_app()

    opt = ConfigOption('.configs.config', whitelist_keys_from_mappings=True)
    opt2 = ConfigOption('./configs/config.cfg')

    app.configure(opt, opt2, whitelist=['THIRD_OPTION'])

    # ensure that the whitelist is applied to the first ConfigOption, but not
    # the second, since it didn't have the whitelist_keys call
    assert app.config['FLEAKER_CONFIG_CFG_LOADED']
    assert app.config['THIRD_OPTION'] == 'loaded from config.cfg'
    assert 'FLEAKER_CONFIG_PY_LOADED' not in app.config, 'This option doesnt work on files...'


@pytest.mark.parametrize("config_file", MISSING_CONFIGS)
def test_config_config_option_does_not_override(config_file):
    """Ensure a ConfigOption with ignore_missing does not imply ignore_missing
    over the entire call.
    """
    app = _create_app()

    opt = ConfigOption(config_file, ignore_missing=True)

    with pytest.raises(ConfigurationError):
        app.configure(opt, '.configs.config', '.configs.really_dne')


def test_config_config_option_whitelist():
    # @TODO: Test where we use whitlist and whitelist_keys_from_mappings via
    # ConfigOption and not configure
    pytest.fail()


def test_enable_doctest():
    pytest.fail("Please enable doctests for ConfigOptions' update_options")


def test_config_option_update_options():
    # @TODO: Test this method; one test that tests both copy as True and False
    # and provides all args to ConfigOption in their non-default value
    pytest.fail()


@pytest.mark.parametrize("config_file", MISSING_CONFIGS)
def test_config_import_missing(config_file):
    """Ensure that a proper error message is thrown if we can't find a config.
    """
    app = _create_app()

    # @TODO: This needs a better error message.
    full_path = os.path.join(os.path.dirname(__file__), config_file)
    err_msg = ("Could not find configuration item '{}'! Searched path: "
               "{}.".format(config_file, full_path))
    with pytest.raises(ConfigurationError) as exc:
        app.configure(config_file)

    # now ensure exception inheritance is fine
    assert isinstance(exc.value, FleakerException)
    # @TODO: Or should this be an IOError? Either way, pick only one base
    # exception inheritance, and document that. I think IOError makes more
    # sense... It CAN be both... but that seems aggressive
    assert isinstance(exc.value, IOError)
    assert str(exc.value) == err_msg


@pytest.mark.parametrize("config_file", MISSING_MODULES)
def test_config_import_missing(config_file):
    """Ensure that a proper error message is thrown if we can't find a config.
    """
    app = _create_app()

    # @TODO: This needs a better error message.
    path = config_file[1:] if config_file.startswith('.') else config_file
    path = path.replace('.', os.path.sep) + '.py'
    full_path = os.path.join(os.path.dirname(__file__), path)
    err_msg = ("Could not find configuration item '{}'! Searched path: "
               "{}.".format(config_file, full_path))
    with pytest.raises(ConfigurationError) as exc:
        app.configure(config_file)

    # now ensure exception inheritance is fine
    assert isinstance(exc.value, FleakerException)
    # @TODO: Or should this be an IOError? Either way, pick only one base
    # exception inheritance, and document that. I think IOError makes more
    # sense... It CAN be both... but that seems aggressive
    assert isinstance(exc.value, IOError)
    assert str(exc.value) == err_msg


@pytest.mark.parametrize("config_file", BAD_PERMISSION_CONFIGS)
def test_config_import_no_owner(config_file, mocker):
    """Ensure that a helpful error message is thrown if we can't read a config
    file.
    """
    app = _create_app()

    io_err_msg = ("[Errno 13] Permission denied: "
                  "'tests/configs/{}'".format(config_file))
    mocker.patch('flask.config.open'.format(__name__), side_effect=IOError(io_err_msg))

    full_path = os.path.join(os.path.dirname(__file__), config_file)
    err_msg = ("Found configuration item '{}' at {} but could not load it! Are"
               " the permissions properly configured?".format(config_file,
                                                              full_path))

    with pytest.raises(ConfigurationError) as exc:
        app.configure(config_file)
    # @TODO: Does this work on Windows?

    # now ensure exception inheritance is fine
    assert isinstance(exc.value, FleakerException)
    assert isinstance(exc.value, IOError)
    assert str(exc.value) == err_msg

    # @TODO: Do we need a ConfigOption to ignore this? Possibly


@pytest.mark.parametrize('config_file', BAD_PERMISSION_MODULES)
def test_config_import_module_no_owner(config_file, mocker):
    """Ensure that a helpful error message is thrown if we can't import a config
    file.
    """
    app = _create_app()

    mocker.patch.dict('sys.modules', {config_file: None})

    path = config_file[1:] if config_file.startswith('.') else config_file
    path = path.replace('.', os.path.sep) + '.py'
    full_path = os.path.join(os.path.dirname(__file__), path)
    err_msg = ("Found configuration item '{}' at {} but could not load it! Are"
               " the permissions properly configured?".format(config_file,
                                                              full_path))

    with pytest.raises(ConfigurationError) as exc:
        app.configure(config_file)

    # now ensure exception inheritance is fine
    assert isinstance(exc.value, FleakerException)
    assert isinstance(exc.value, IOError)
    assert str(exc.value) == err_msg
