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

import fleaker

import tests.configs.settings as settings


def _create_app():
    """Utility function to create the app for config testing.

    It requires a bit more work than standard test app creation (but not much).

    Returns:
        fleaker.App: The standard App we just created.
    """
    return fleaker.App('tests')


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


def test_config_import_missing():
    """Ensure that a proper error message is thrown if we can't find a config.
    """
    import pytest
    pytest.fail()


def test_config_import_no_owner():
    """Ensure that a helpful error message is thrown if we can't read a config
    file.
    """
    import pytest
    pytest.fail()
