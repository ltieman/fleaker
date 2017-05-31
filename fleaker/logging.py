# -*- coding: utf-8 -*-
"""
fleaker.logging
~~~~~~~~~~~~~~~

This module provides an app mixin that implements a configurable custom logging
extension for Flask. These logs will be colorized depending on the log level
and will contain slightly more information than the built in Flask one. This
module also makes rotating file logs a lot easier to user out of the box.

In order to make maximum use of this module, there are some application
configuration variables that you should be aware of:

* ``LOGGING_FORMATTER``: This value must be an instance of
  ``logging.Formatter`` and will define how logs written to the stream are
  displayed.
* ``LOGGING_DEFAULT_LEVEL``: This is the minimum level at which logs should be
  printed to the stream. If the app is in debug mode, this will be set to
  ``logging.DEBUG`` otherwise it will be ``logging.INFO``.
* ``LOGGING_FILE_PATH``: This is a full path to where a log file for this
  application. By default, this is ``None`` so that no log file is created.
* ``LOGGING_FILE_MAX_SIZE``: This is the size, in bytes, of how large a log
  file can get before it is rotated. This defaults to 10MB.
* ``LOGGING_FILE_MAX_BACKUPS``: This is number of log file backups that must be
  retained. This defaults to 5.
* ``LOGGING_FILE_FORMATTER``: This is the formatter that will be used for file
  based logs. It must be an instance of ``logging.Formatter``. By default, this
  will be the same format as ``LOGGING_FORMATTER`` without any colors escapes.
"""

from __future__ import absolute_import

import logging
import os

from logging.handlers import RotatingFileHandler

from .base import BaseApplication


class FleakerLogFormatter(logging.Formatter):
    """
    A log formatter to add coloring to logs based on the level of the message.
    """

    class TermColors(object):
        # blue
        INFO = '\033[94m'
        # green
        DEBUG = '\033[92m'
        # yellow
        WARNING = '\033[93m'
        # red
        ERROR = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    def format(self, record):
        """Format the log record."""
        levelname = getattr(record, 'levelname', None)
        record.levelcolor = ''
        record.endlevelcolor = ''

        if levelname:
            level_color = getattr(self.TermColors, levelname, '')
            record.levelcolor = level_color
            record.endlevelcolor = self.TermColors.ENDC if level_color else ''

        return super(FleakerLogFormatter, self).format(record)


DEFAULT_FORMATTER = FleakerLogFormatter(
    ('-' * 80 + '\n') +
    '%(levelcolor)s[%(asctime)s] %(levelname)s in %(module)s ' +
    '[%(pathname)s:%(lineno)d]:\n' +
    '%(endlevelcolor)s%(message)s\n' +
    ('-' * 80)
)
DEFAULT_FILE_FORMATTER = FleakerLogFormatter(
    '-' * 80 + '\n' +
    '[%(asctime)s] %(levelname)s in %(module)s ' +
    '[%(pathname)s:%(lineno)d]:\n' +
    '%(message)s\n' +
    ('-' * 80)

)


class LoggingAwareApp(BaseApplication):
    """Application extension that will enable better default logging.

    This application mixin is added to ``Fleaker.App`` by default.
    """

    def __init__(self, *args, **kwargs):
        super(LoggingAwareApp, self).__init__(*args, **kwargs)

        default_level = (logging.DEBUG if self.config['DEBUG']
                         else logging.INFO)

        self.config.setdefault('LOGGING_FORMATTER', DEFAULT_FORMATTER)
        self.config.setdefault('LOGGING_DEFAULT_LEVEL', default_level)
        self.config.setdefault('LOGGING_FILE_PATH', None)
        self.config.setdefault('LOGGING_FILE_MAX_SIZE', 10 * 1024 * 1024)
        self.config.setdefault('LOGGING_FILE_MAX_BACKUPS', 5)
        self.config.setdefault('LOGGING_FILE_LEVEL', logging.WARNING)
        self.config.setdefault('LOGGING_FILE_FORMATTER',
                               DEFAULT_FILE_FORMATTER)

        self.add_post_configure_callback(self.register_logging)

    def register_logging(self, *args):
        # nuke the existing handlers, which should be Flask's default
        # DebugHandler and ProductionHandler and that's it (all those handlers
        # do is intelligently set the log level based on the DEBUG config's
        # value)
        del self.logger.handlers[:]

        if not os.environ.get('WERKZEUG_RUN_MAIN'):
            # if we're running this in invoke... the first request isn't going
            # to run, ever (because... obvious reasons), so just call this
            # manually
            self._setup_logging()
        else:
            # in Flask! We will get a first request
            self.before_first_request(self._setup_logging)

        # in non-debug configurations, catch all Exceptions and render the
        # relevant error page (a string for now). If we don't do this, then
        # Flask will NOT return a response to the WSGI handler and you get an
        # ugly 502 Gateway error, that tends to confuse a lot of people (they
        # think the whole server is down, for example).
        if not self.config['DEBUG']:
            self.errorhandler(500)(self.internal_server_error)

        self._register_file_logger()

    def _register_file_logger(self):
        if not self.config['LOGGING_FILE_PATH']:
            return

        formatter = self.config['LOGGING_FILE_FORMATTER']
        handler = RotatingFileHandler(
            self.config['LOGGING_FILE_PATH'],
            maxBytes=self.config['LOGGING_FILE_MAX_SIZE'],
            backupCount=self.config['LOGGING_FILE_MAX_BACKUPS']
        )
        handler.setLevel(self.config['LOGGING_FILE_LEVEL'])

        if isinstance(formatter, logging.Formatter):
            handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def internal_server_error(self, exception):
        """
        Standard error handler for 500's.
        Will log stack trace and return a simple page with text.
        """
        self.logger.exception(exception)
        return 'Internal Server Error', 500

    def _setup_logging(self):
        default_level = self.config['LOGGING_DEFAULT_LEVEL']

        # Fix for https://github.com/getsentry/raven-python/issues/946 which
        # is caused by https://github.com/pallets/flask/commit/e00e2c22aadf9e5b9dc353c31f1b70dad488b47a
        self.logger.propagate = True

        # Register the stream handler
        handler = logging.StreamHandler()
        handler.setLevel(default_level)

        # Set the custom formatter, if it exists
        formatter = self.config['LOGGING_FORMATTER']

        if isinstance(formatter, logging.Formatter):
            handler.setFormatter(formatter)

        loggers = [self.logger]

        # sometimes the Werkzeug logger gets it's handlers CLOBBERED and can't
        # log anything, this is a quick fix for that
        # @TODO: Why do those handlers get clobbered?!?!?!?
        werkzeug_logger = logging.getLogger('werkzeug')

        if not len(werkzeug_logger.handlers):
            loggers.append(werkzeug_logger)

        for logger in loggers:
            logger.addHandler(handler)
            logger.setLevel(default_level)

        if not isinstance(formatter, logging.Formatter):
            self.logger.warning("The value of LOGGING_FORMATTER must be an "
                                "instance of logging.Formatter")
