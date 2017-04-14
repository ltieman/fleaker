# ~*~ coding: utf-8 ~*~
"""Unit tests for the JSON Schema Marshmallow class."""

from os import remove
from tempfile import NamedTemporaryFile

import pytest

from marshmallow import fields

from fleaker.marshmallow import (
    FleakerJSONSchema, Schema, ForeignKeyField, REQUIRED, STR_REQUIRED
)


class UserSchema(Schema):
    first_name = fields.String(**STR_REQUIRED)
    last_name = fields.String(**STR_REQUIRED)
    company_id = ForeignKeyField(**REQUIRED)

    class Meta(object):
        json_schema_filename = 'user.json'


@pytest.mark.parametrize('schema', (
    UserSchema,
    UserSchema(),
    'tests.marshmallow.test_json_schema.UserSchema',
))
def test_generate_json_schema(schema):
    """Ensure that a JSON Schema can be generated from a Marshmallow schema."""
    json_schema = FleakerJSONSchema.generate_json_schema(schema)
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
    FleakerJSONSchema().write_schema_to_file(
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
        FleakerJSONSchema.write_schema_to_file(schema)


@pytest.mark.parametrize('field_module,field_class', (
    ('fleaker.marshmallow.fields.pendulum', 'PendulumField'),
    ('fleaker.marshmallow.fields.arrow', 'ArrowField'),
    ('fleaker.marshmallow.fields.phone_number', 'PhoneNumberField'),
))
def test_fleaker_field_output(field_module, field_class):
    """Ensure that Fleaker custom fields output the right mappings."""
    try:
        field_obj = getattr(pytest.importorskip(field_module), field_class)
    except (ImportError, AttributeError):
        pytest.mark.skip("Test run doesn't support {}.".format(field_class))

    class TestSchema(Schema):
        test_field = field_obj()

    schema = TestSchema()
    json_schema = FleakerJSONSchema.generate_json_schema(schema)

    assert (schema.fields['test_field']._jsonschema_type_mapping() ==
            json_schema['properties']['test_field'])
