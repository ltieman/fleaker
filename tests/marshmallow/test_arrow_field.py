# ~*~ coding: utf-8 ~*~
"""Unit tests for the Arrow Marshmallow field."""

import pytest

arrow = pytest.importorskip('arrow')

from marshmallow import ValidationError

from fleaker._compat import text_type
from fleaker.marshmallow import ArrowField, Schema


class ArrowSchema(Schema):
    time = ArrowField(format='iso')


def test_arrow_field_loads():
    """Ensure that the ArrowField can deserialize data."""
    schema = ArrowSchema()
    now = arrow.utcnow()
    payload = {'time': text_type(now)}
    serialized = schema.load(payload).data

    assert isinstance(serialized['time'], arrow.Arrow)
    assert now == serialized['time']


def test_arrow_field_dumps():
    """Ensure that the ArrowField can serialize data."""
    schema = ArrowSchema()
    now = arrow.utcnow()
    payload = {'time': now}
    serialized = schema.dump(payload).data

    assert serialized['time'] == text_type(now)


def test_arrow_field_timezone_validation():
    """Ensure that the ArrowField can validate timezones."""
    schema = ArrowSchema(context={'timezone': 'UTC'})
    now = arrow.utcnow().to('America/New_York')
    payload = {'time': text_type(now)}
    error_msg = {
        'time': "The provided datetime is not in the UTC timezone."
    }

    with pytest.raises(ValidationError, message=error_msg):
        schema.load(payload).data


def test_arrow_field_does_not_convert_when_told_not_to_like_a_good_boy():
    """Ensure that ArrowField won't convert dates when told not to."""
    schema = ArrowSchema(context={'convert_dates': False})
    now = arrow.utcnow()
    payload = {'time': text_type(now)}
    serialized = schema.load(payload).data

    assert serialized['time'] == payload['time']
