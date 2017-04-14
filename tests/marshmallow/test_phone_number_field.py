# ~*~ coding: utf-8 ~*~
"""Unit tests for the Phone Number Marshmallow field."""

import pytest

pytest.importorskip('phonenumber')

from marshmallow import ValidationError
from marshmallow.fields import String

from fleaker.marshmallow import PhoneNumberField, Schema


class PhoneNumberSchema(Schema):
    text = String(allow_none=True)
    phone = PhoneNumberField(allow_none=True)


@pytest.mark.parametrize('number,expected,strict,passes', (
    ('1-412-422-9994', '+1 412-422-9994', False, True),
    ('1-412-422-9994', None, True, False),
    ('+1-412-422-9994', '+1 412-422-9994', True, True),
    ('+1-555-555-5555', None, True, False)
))
def test_phone_number_field_load(number, expected, strict, passes):
    """Ensure that the Phone Number field can format numbers correctly."""
    schema = PhoneNumberSchema(context={'strict_phone_validation': strict})
    payload = {'phone': number}

    if passes:
        deserialized = schema.load(payload).data
        assert deserialized['phone'] == expected

        serialized = schema.dump(deserialized).data
        assert serialized['phone'] == expected
    else:
        error_msg = {
            'phone': [("The value for phone ({}) is not a valid phone "
                       "number.".format(number))]
        }

        with pytest.raises(ValidationError, message=error_msg):
            schema.load(payload)


@pytest.mark.parametrize('payload', (
    {'phone': None},
    {'phone': ''},
    {'text': ''},
    {},
))
def test_phone_number_early_exit(payload):
    """Ensure that a null phone number isn't parsed."""
    schema = PhoneNumberSchema()
    serialized = schema.load(payload).data

    assert not serialized.get('phone')

    deserialized = schema.dump(serialized).data

    assert not deserialized.get('phone')
