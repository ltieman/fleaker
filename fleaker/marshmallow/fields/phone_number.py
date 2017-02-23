# ~*~ coding: utf-8 ~*~
"""Module that defines a Marshmallow field for working with phone numbers."""

import re

import phonenumbers

from marshmallow import ValidationError, fields

from .mixin import FleakerFieldMixin


class PhoneNumberField(fields.String, FleakerFieldMixin):
    """Marshmallow field that can format and validate phone numbers.

    All validation is done with Google's libphonenumber_ and is strictly
    optional. The enforcement of this validation can be controled at the field
    level and at the context level as well. It should be noted that all keyword
    arguments for this field can be overriden at runtime by supplying these
    keys to the schema's ``context``.

    Keyword Args:
        strict_validation (bool): Should the number be strictly validated? This
            means that not only will the number be parsed hard, it will be
            validated against libphonenumber and a ValidationError will be
            raised if it's not valid. This defaults to false.
        strict_region (bool): Should the region be strictly validated? This
            means that a leading country code with a ``+`` must be provided.
            This defaults to the value of ``strict_validation``. If you want to
            validate the number but are unable to provide the ``+``, set
            ``strict_validation`` to ``True`` and ``strict_region`` to
            ``False``. If this is False, the phone number will automatically be
            converted to the value of ``region`` before validating.
        region (str): This is the region the number should be validated
            against. This is only used if ``strict_validation`` is false and it
            defaults to `US`.
        phone_number_format (phonenumbers.PhoneNumberFormat): This is the
            format in which to format the phone number. It defaults to
            ``phonenumbers.PhoneNumberFormat.INTERNATIONAL``.

    .. _libphonenumber: https://github.com/daviddrysdale/python-phonenumbers
    """

    def _jsonschema_type_mapping(self):
        """Define the JSON Schema type for this field."""
        return {
            'type': 'string',
        }

    def _format_phone_number(self, value, attr):
        """Format and validate a phone number."""
        strict_validation = self.get_field_value(
            'strict_phone_validation',
            default=False
        )
        strict_region = self.get_field_value(
            'strict_phone_region',
            default=strict_validation
        )
        region = self.get_field_value('region', 'US')
        phone_number_format = self.get_field_value(
            'phone_number_format',
            default=phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )

        # Remove excess special chars, except for the plus sign
        stripped_value = re.sub(r'[^\w+]', '', value)

        try:
            if not stripped_value.startswith('+') and not strict_region:
                phone = phonenumbers.parse(stripped_value, region)
            else:
                phone = phonenumbers.parse(stripped_value)

            if (not phonenumbers.is_possible_number(phone) or
                    not phonenumbers.is_valid_number(phone) and
                    strict_validation):
                raise ValidationError(
                    "The value for {} ({}) is not a valid phone "
                    "number.".format(attr, value)
                )

            return phonenumbers.format_number(phone, phone_number_format)

        except phonenumbers.phonenumberutil.NumberParseException as exc:
            if strict_validation or strict_region:
                raise ValidationError(exc)

    def _deserialize(self, value, attr, data):
        """Format and validate the phone number using libphonenumber."""
        if value:
            value = self._format_phone_number(value, attr)

        return super(PhoneNumberField, self)._deserialize(value, attr, data)

    def _serialize(self, value, attr, obj):
        """Format and validate the phone number user libphonenumber."""
        value = super(PhoneNumberField, self)._serialize(value, attr, obj)

        if value:
            value = self._format_phone_number(value, attr)

        return value
