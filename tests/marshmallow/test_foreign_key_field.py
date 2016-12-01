# ~*~ coding: utf-8 ~*~
"""Unit test for the Foreign Key Marshmallow field."""

from fleaker.marshmallow import ForeignKeyField, Schema


class ForeignKeySchema(Schema):
    thing_id = ForeignKeyField()


def test_foreign_key_field_loads():
    """Ensure that the id portion of the data is removed when loaded."""
    schema = ForeignKeySchema()
    payload = {'thing_id': 1}
    serialized = schema.load(payload).data

    assert 'thing_id' not in serialized
    assert serialized['thing'] == payload['thing_id']


def test_foreign_key_dumps():
    """Ensure that the id portion of the data is grabbed from the object."""
    class Thing(object):
        id = 1

    schema = ForeignKeySchema()
    payload = {'thing': Thing()}
    serialized = schema.dump(payload).data

    assert serialized['thing_id'] == 1
