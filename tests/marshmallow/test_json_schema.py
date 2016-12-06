# ~*~ coding: utf-8 ~*~
"""Unit tests for the JSON Schema Marshmallow class."""

from os import remove
from tempfile import NamedTemporaryFile

import pytest

from marshmallow import fields

from fleaker.marshmallow import (
    JSONSchema, Schema, PhoneNumberField, PendulumField, ArrowField,
    ForeignKeyField, REQUIRED, STR_REQUIRED
)


class UserSchema(Schema):
    first_name = fields.String(**STR_REQUIRED)
    last_name = fields.String(**STR_REQUIRED)
    phone = PhoneNumberField(**REQUIRED)
    company_id = ForeignKeyField(**REQUIRED)
    joined = PendulumField(format='iso', **REQUIRED)
    last_login = ArrowField(allow_none=True, format='iso')

    class Meta(object):
        json_schema_filename = 'user.json'


@pytest.mark.parametrize('schema', (
    UserSchema,
    UserSchema(),
    'tests.marshmallow.test_json_schema.UserSchema',
))
def test_generate_json_schema(schema):
    """Ensure that a JSON Schema can be generated from a Marshmallow schema."""
    json_schema = JSONSchema.generate_json_schema(schema)
    schema = UserSchema()

    for key, field in schema.fields.items():
        assert (key in json_schema['required']) is field.required


@pytest.mark.parametrize('schema,folder,file_pointer', (
    (UserSchema, None, NamedTemporaryFile(mode='w', suffix='.json')),
    (UserSchema(), '/tmp', None),
    ('tests.marshmallow.test_json_schema.UserSchema', None,
     NamedTemporaryFile(mode='w', suffix='.json')),
))
def test_write_json_schema_to_file(schema, folder, file_pointer):
    """Ensure that JSON schemas can be written to a file."""
    JSONSchema().write_schema_to_file(
        schema,
        file_pointer=file_pointer,
        folder=folder,
    )

    # Cleanup in the test cause I'm too lazy to make a fixture
    try:
        remove('/tmp/user.json')
    except OSError:
        pass

    try:
        file_pointer.close()
    except AttributeError:
        pass


@pytest.mark.parametrize('schema', (object(), 'os.path.join'))
def test_only_marshmallow_schemas_allowed(schema):
    """Ensure that only Marshmallow schemas are allowed."""
    with pytest.raises(TypeError):
        JSONSchema.write_schema_to_file(schema)
