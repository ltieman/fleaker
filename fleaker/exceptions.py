# ~*~ coding: utf-8 ~*~
"""
fleaker.exceptions
~~~~~~~~~~~~~~~~~~

Provides test for the common configuration options.

:copyright: (c) 2016 by Croscon Consulting, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""


class FleakerException(Exception):
    """Baseclass for all custom exceptions thrown from Fleaker.

    Should NEVER be thrown on it's own unless something has gone horribly
    wrong.
    """

    def __init__(self, msg=None, status_code=None):
        """Construct a base Fleaker Exception, accepting an optional kwarg of
        ``status_code`` to set the status code on the response.
        """
        self.status_code = status_code
        self.message = msg

        super(Exception, self).__init__(self, msg)
