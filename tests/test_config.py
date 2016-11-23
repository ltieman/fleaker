# ~*~ coding: utf-8 ~*~
"""
tests.test_config
~~~~~~~~~~~~~~~~~

Provides test for the common configuration options.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import fleaker


def test_configure():
    """Ensure generic configure method works."""
    app = fleaker.App(__name__)
    app.configure('.configs.settings', '.configs.overrides')

    assert app.config['CANARY']
    assert app.config['SECRET_KEY'] == 'bar'
    assert app.config['THIRD_OPTION'] == 'three'
    assert app.config['TEST_KEY'] == 'foo'


def test_configure_from_environment():
    """Ensure this one method properly configures based on the entire
    environment.
    """
    # @TODO: Finish more configure tests. Add some for more esoteric
    # configuration methods and test the configuration methods directly
