# ~*~ coding: utf-8 ~*~
"""Unit tests for the Pendulum Marshmallow field."""

import pendulum
import pytest

from marshmallow import ValidationError

from fleaker._compat import text_type
from fleaker.marshmallow import PendulumField, Schema


class PendulumSchema(Schema):
    time = PendulumField(format='iso', allow_none=True)


def test_pendulum_field_loads():
    """Ensure that the PendulumField can deserialize data."""
    schema = PendulumSchema()
    now = pendulum.utcnow()
    payload = {'time': text_type(now)}
    serialized = schema.load(payload).data

    assert isinstance(serialized['time'], pendulum.Pendulum)
    assert serialized['time'] == now


def test_pendulum_field_dumps():
    """Ensure that the PendulumField can serialize data."""
    schema = PendulumSchema()
    now = pendulum.utcnow()
    payload = {'time': now}
    serialized = schema.dump(payload).data

    assert serialized['time'] == text_type(now)


def test_pendulum_field_timezone_validation():
    """Ensure that the PendulumField can validate timezones."""
    schema = PendulumSchema(context={'timezone': 'UTC'})
    now = pendulum.now('America/New_York')
    payload = {'time': text_type(now)}
    error_msg = {
        'time': "The provided datetime is not in the UTC timezone."
    }

    with pytest.raises(ValidationError, message=error_msg):
        schema.load(payload).data


def test_pendulum_field_does_not_convert_when_told_not_to_like_a_good_boy():
    """Ensure that PendulumField won't convert dates when told not to."""
    schema = PendulumSchema(context={'convert_dates': False})
    now = pendulum.utcnow()
    payload = {'time': text_type(now)}
    serialized = schema.load(payload).data

    assert serialized['time'] == payload['time']


def test_pendulum_field_load_null():
    """Ensure that a null value can be loaded into a PendulumField."""
    schema = PendulumSchema()
    payload = {'time': None}
    serialized = schema.load(payload).data

    assert serialized['time'] is None
