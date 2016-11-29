# ~*~ coding: utf-8 ~*~
"""
tests.test_exceptions
~~~~~~~~~~~~~~~~~

Provides tests for the custom Exceptions Fleaker implements.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import pytest

from fleaker import exceptions


# please list all custom exceptions here for a quick test
@pytest.mark.parametrize('spec', [
    (exceptions.FleakerException, 'Message', 401),
])
def test_exceptions_basic_args(spec):
    """Ensure we can raise Exceptions with a status code and message.
    """
    exc_type, msg, code = spec

    with pytest.raises(exc_type) as exc:
        raise exc_type(msg, status_code=code)

    assert type(exc.value) is exc_type
    assert exc.value.message == msg
    assert exc.value.status_code == code
