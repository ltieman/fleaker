# ~*~ coding: utf-8 ~*~
"""Unit tests for the Phone Number Marshmallow field."""

import pytest

from marshmallow import ValidationError

from fleaker.marshmallow import PhoneNumberField, Schema


class PhoneNumberSchema(Schema):
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
        serialized = schema.load(payload).data
        assert serialized['phone'] == expected
    else:
        error_msg = {
            'phone': [("The value for phone ({}) is not a valid phone "
                       "number.".format(number))]
        }

        with pytest.raises(ValidationError, message=error_msg):
            schema.load(payload)


def test_phone_number_early_exit():
    """Ensure that a null phone number isn't parsed."""
    schema = PhoneNumberSchema()
    payload = [
        {'phone': None},
        {'phone': ''},
        {}
    ]
    serialized = schema.load(payload, many=True).data

    for item in serialized:
        assert not item.get('phone')
