"""Unit tests for the custom logging in Fleaker."""

import os
import tempfile

import pytest

from fleaker import App


@pytest.fixture
def temp_log_file():
    log_file_path = os.path.join(tempfile.gettempdir(), 'fleaker-test.log')
    yield log_file_path
    os.unlink(log_file_path)


@pytest.mark.parametrize('level', (
    'debug',
    'info',
    'warning',
    'error',
))
def test_logging(app, level):
    """Ensure that each level can be logged."""
    getattr(app.logger, level)("Test message")
    assert len(app.logger.handlers) == 1


def test_file_logging(temp_log_file):
    settings = {'LOGGING_FILE_PATH': temp_log_file}
    app = App('logging_file_test')
    app.configure(settings)

    assert len(app.logger.handlers) == 2

    # Now, let's log
    app.logger.info("This won't be in the log")
    app.logger.warning("This will be in the log")
    app.logger.error("This error will be in the log")

    with open(temp_log_file, 'r') as fp:
        logs = fp.read()
        assert "This won't be in the log" not in logs
        assert "This will be in the log" in logs
        assert "This error will be in the log" in logs
