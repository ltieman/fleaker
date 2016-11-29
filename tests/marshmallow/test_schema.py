# ~*~ coding: utf-8 ~*~
"""Unit tests for the base schema Fleaker provides."""

import pytest

from marshmallow import ValidationError, fields

from fleaker.marshmallow import Schema


class SchemaTest(Schema):
    """Just a simple test schema for this file."""
    name = fields.String()


def test_load_schema_normally():
    """Ensure that data can be loaded into the schema normally."""
    schema = SchemaTest()
    payload = {
        'name': 'Bob Blah',
    }
    serialized = schema.load(payload).data

    assert serialized['name'] == payload['name']


def test_invalid_fields_error_out():
    schema = SchemaTest()
    payload = {
        'name': 'Bob Blah',
        'invalid': 'field',
    }

    with pytest.raises(ValidationError,
                       message={'invalid': ['Invalid field']}):
        schema.load(payload)
