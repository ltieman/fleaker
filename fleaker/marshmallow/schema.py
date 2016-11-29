# ~*~ coding: utf-8 ~*~
"""Module that defines a strict but fair base Marshmallow schema."""

from marshmallow import ValidationError, Schema as _Schema, validates_schema


class Schema(_Schema):
    """Base schema that defines sensible default rules for Marshmallow.

    The single most important thing that this module provides is strict
    validation by default. That means, whenever an error is encountered, it
    raises a :class:`marshmallow.ValidationError` instead of going about things
    silently and storing the errors on the ``errors`` attribute of the
    serialized data. In practice, this is a super powerful pattern because you
    can let that exception bubble all the way up to your app's errorhandler and
    boom, you've got fancy and consistent error reporting without doing
    anything extra.
    """

    def __init__(self, **kwargs):
        super(Schema, self).__init__(**kwargs)

        self.strict = True

        if self.context.get('strict'):
            self.strict = self.context.get('strict')

    @validates_schema(pass_original=True)
    def invalid_fields(self, data, original_data):
        """Validator that checks if any keys provided aren't in the schema.

        Say your schema has support for keys ``a`` and ``b`` and the data
        provided has keys ``a``, ``b``, and ``c``. When the data is loaded into
        the schema, a :class:`marshmallow.ValidationError` will be raised
        informing the developer that excess keys have been provided.

        Raises:
            marshmallow.ValidationError: Raised if extra keys exist in the
                passed in data.
        """
        errors = []

        for field in original_data:
            # Skip iterables because they will mess up this code hard
            if isinstance(field, (set, list, tuple, dict)):
                continue

            if field not in self.fields.keys():
                errors.append(field)

        if errors:
            raise ValidationError("Invalid field", field_names=errors)
