"""Module that provides a mixin that can help define Marshmallow fields."""

from marshmallow import fields

from fleaker.constants import MISSING


class FleakerFieldMixin(fields.Field):

    def get_field_value(self, key, default=MISSING):
        """Method to fetch a value from either the fields metadata or the
        schemas context, in that order.

        Args:
            key (str): The name of the key to grab the value for.

        Keyword Args:
            default (object, optional): If the value doesn't exist in the
                schema's ``context`` or the field's ``metadata``, this value
                will be returned. By default this will be ``MISSING``.

        Returns:
            object: This will be the correct value to use given the parameters.
        """
        meta_value = self.metadata.get(key)
        context_value = self.context.get(key)

        if context_value is not None:
            return context_value
        elif meta_value is not None:
            return meta_value

        return default
