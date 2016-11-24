"""Unit tests for ``fleaker.MissingSentinel``."""

import pytest

from fleaker import MissingSentinel


def test_missing_sentinel():
    """Ensure that the MissingSentinel works as expected."""
    MISSING = MissingSentinel()

    # The sentinel can be evaluated loosely as a False value
    assert bool(MISSING) is False
    assert not MISSING

    if MISSING:
        pytest.fail(
            "MissingSentinel shouldn't evaluate to True in a if statement."
        )

    # But the sentinel is not False though
    assert MISSING is not False

    # The iterable has a length of 0
    assert len(MISSING) == 0
