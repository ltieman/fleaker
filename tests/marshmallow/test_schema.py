# ~*~ coding: utf-8 ~*~
"""Unit tests for the base schema Fleaker provides."""

import pytest

from marshmallow import ValidationError, fields

try:
    import peewee
except ImportError:
    peewee = None

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
    """Ensure that ValidationErrors are raised when a field doesn't belong."""
    schema = SchemaTest()
    payload = {
        'name': 'Bob Blah',
        'invalid': 'field',
    }

    with pytest.raises(ValidationError,
                       message={'invalid': ['Invalid field']}):
        schema.load(payload)


def test_contextual_strict_setting():
    """Ensure that schema strictness can be toggled via the context."""
    # By default, schemas are strict
    assert SchemaTest().strict

    # But they can be toggled via a kwarg
    assert not SchemaTest(strict=False).strict

    # It can also be toggled via the context, which some might find useful
    assert not SchemaTest(context={'strict': False}).strict


@pytest.mark.skipif(peewee is None,
                    reason=("Some test envs don't have peewee."))
def test_make_instance():
    """Ensure that the schema's make instance works properly."""
    from peewee import Model, CharField

    class User(Model):
        name = CharField(max_length=255)

    class UserSchema(Schema):
        name = fields.String()

        class Meta:
            model = User

    data = {'name': 'Bob Blah'}
    user = UserSchema.make_instance(data)

    assert isinstance(user, User)
    assert user.name == data['name']


def test_make_instance_fails():
    """Ensure that make_instance fail's if no model is specified."""
    with pytest.raises(AttributeError):
        SchemaTest.make_instance({'name': 'Bob Blah'})
