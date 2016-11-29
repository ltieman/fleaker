# ~*~ coding: utf-8 ~*~
"""Module that defines a Marshmallow field that deserializes a date string into
an Pendulum object.
"""

from datetime import datetime

import pendulum

from marshmallow import ValidationError, fields


class PendulumField(fields.DateTime):
    """Marshmallow field that deserialzes datetimes into Pendulum objects.

    Has the same output on dump as the standard DateTime field. Accepts the
    same kwargs on init.

    This field is effected by the following schema context variables:

    - ``'convert_dates'``: This will prevent the date string from being
        converted into a Pendulum object. This can be useful if you're going to
        be double deserialzing the value in the course of the request. This is
        needed for Webargs. By default, dates will be converted.

    Keyword Args:
        timezone (str): The timezone that the datetime must be in. If it
            doesn't match, a ``marshmallow.ValidationError`` is raised.
    """

    def _jsonschema_type_mapping(self):
        """Define the JSON Schema type for this field."""
        result = {
            'type': 'string',
            'format': 'date-time',
        }

        # @TODO This is needed because marshmallow jsonschema doesn't support
        # setting these attributes like it does with built-ins. Fix this
        # upstream and remove this code.
        if self.metadata.get('metadata', {}).get('description'):
            result['description'] = self.metadata['metadata']['description']

        if self.metadata.get('metadata', {}).get('title'):
            result['title'] = self.metadata['metadata']['title']

        return result

    def _deserialize(self, value, attr, obj):
        """Deserializes a string into a Pendulum object."""
        if not self.context.get('convert_dates', True):
            return value

        value = super(PendulumField, self)._deserialize(value, attr, value)
        timezone = self.metadata.get('timezone')

        if isinstance(value, datetime):
            target = pendulum.instance(value)

            if timezone and (target != target.in_timezone(timezone)):
                raise ValidationError(
                    "The provided datetime is not in the "
                    "{} timezone".format(timezone)
                )

            return target

        return value
