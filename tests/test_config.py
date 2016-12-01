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

from fleaker.config import MultiStageConfigurableApp

import tests.configs.settings as settings

from tests._compat import mock


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
