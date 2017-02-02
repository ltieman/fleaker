# ~*~ coding: utf-8 ~*~
"""Module that defines a strict but fair base Marshmallow schema."""

from marshmallow import ValidationError, validates_schema

from .extension import marsh


class Schema(marsh.Schema):
    """Base schema that defines sensible default rules for Marshmallow.

    The single most important thing that this module provides is strict
    validation by default. That means, whenever an error is encountered, it
    raises a :class:`marshmallow.ValidationError` instead of going about things
    silently and storing the errors on the ``errors`` attribute of the
    serialized data. In practice, this is a super powerful pattern because you
    can let that exception bubble all the way up to your app's errorhandler and
    boom, you've got fancy and consistent error reporting without doing
    anything extra.

    Context Variables:
        strict (bool): The strictness of the schema can be controlled by
            a context variable. This will default to ``True``.

    Attributes:
        Meta.model (peewee.Model|sqlalchemy.Model): The model that this
            schema's ``make_instance`` method should use when serializing the
            data into a model instance.
    """

    def __init__(self, **kwargs):
        super(Schema, self).__init__(**kwargs)

        if kwargs.get('strict') is None:
            self.strict = True

        if self.context.get('strict') is not None:
            self.strict = self.context.get('strict')

    @classmethod
    def make_instance(cls, data):
        """Validate the data and create a model instance from the data.

        Args:
            data (dict): The unserialized data to insert into the new model
                instance through it's constructor.

        Returns:
            peewee.Model|sqlalchemy.Model: The model instance with it's data
                inserted into it.

        Raises:
            AttributeError: This is raised if ``Meta.model`` isn't set on the
                schema's definition.
        """
        schema = cls()

        if not hasattr(schema.Meta, 'model'):
            raise AttributeError("In order to make an instance, a model for "
                                 "the schema must be defined in the Meta "
                                 "class.")

        serialized_data = schema.load(data).data

        return cls.Meta.model(**serialized_data)

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
            # Skip nested fields because they will loop infinitely
            if isinstance(field, (set, list, tuple, dict)):
                continue

            if field not in self.fields.keys():
                errors.append(field)

        if errors:
            raise ValidationError("Invalid field", field_names=errors)
