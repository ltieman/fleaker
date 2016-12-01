# ~*~ coding: utf-8 ~*~
"""Module that defines a Marshmallow field for Peewee's foreign keys."""

from marshmallow import fields

from .mixin import FleakerFieldMixin


class ForeignKeyField(fields.Integer, FleakerFieldMixin):
    """Marshmallow field that can be used with Peewee's foreign key setup.

    Turns a field named ``${relation_name}_id`` into ``${relation_name}`` on
    load, and then back to ``${relation_name}_id`` on dump again.

    This fixes a discrepancy between PeeWee and common API usage. Common API
    usage for DB ID's is to name them ``${relation_name}_id``, for clarity.
    However, PeeWee only accepts FK values set through ``${relation_name}``, so
    fix it!

    This field is effect by the following schema context variable:

    - ``'convert_fks'``: This will prevent the field from being renamed when
        serialized. This is useful if you will be double deserializing the data
        and you don't wanted it converted after the first pass. This flow is
        present for Webargs. By default, this field will rename the key when
        deserialzed.
    """

    def _jsonschema_type_mapping(self):
        """Define the JSON Schema type for this field."""
        return {
            'type': 'number',
            'format': 'integer',
        }

    def _add_to_schema(self, field_name, schema):
        """Set the ``attribute`` attr to the field in question so this always
        gets deserialzed into the field name without ``_id``.

        Args:
            field_name (str): The name of the field (the attribute name being
                set in the schema).
            schema (marshmallow.Schema): The actual parent schema this field
               belongs to.
        """
        super(ForeignKeyField, self)._add_to_schema(field_name, schema)

        if self.get_field_value('convert_fks', default=True):
            self.attribute = field_name.replace('_id', '')

    def _serialize(self, value, attr, obj):
        """Grab the ID value off the Peewee model so we serialize an ID back.
        """
        # this might be an optional field
        if value:
            value = value.id

        return super(ForeignKeyField, self)._serialize(value, attr, obj)
