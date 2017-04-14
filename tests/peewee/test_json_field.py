# ~*~ coding: utf-8 ~*~
"""Unit tests for the JSONField."""

from collections import OrderedDict

import pytest
peewee = pytest.importorskip('peewee')

from werkzeug.datastructures import ImmutableDict

from fleaker.peewee import JSONField


@pytest.mark.parametrize('value,kwargs,dict_type', (
    (None, {}, type(None)),
    ({'key': 'value', 'int': 3}, {}, dict),
    ({'key': 'value', 'int': 3}, {'immutable': False}, dict),
    ({'key': 'value', 'int': 3}, {'ordered': False}, dict),
    ({'key': 'value', 'int': 3}, {'immutable': True}, ImmutableDict),
    ({'key': 'value', 'int': 3}, {'object_pairs_hook': ImmutableDict},
     ImmutableDict),
    ({'key': 'value', 'int': 3}, {'object_hook': ImmutableDict},
     ImmutableDict),
    (ImmutableDict({'key': 'value', 'int': 3}), {'immutable': True},
     ImmutableDict),
    ({'key': 'value', 'int': 3}, {'ordered': True}, OrderedDict),
    ({'key': 'value', 'int': 3}, {'object_pairs_hook': OrderedDict},
     OrderedDict),
    ({'key': 'value', 'int': 3}, {'object_hook': OrderedDict},
     OrderedDict),
    (OrderedDict([('key', 'value'), ('int', 3)]), {'ordered': True},
     OrderedDict),
))
def test_json_field(database, value, kwargs, dict_type):
    """Ensure that the JSONField can load and dump dicts."""
    class JSONModel(peewee.Model):
        data = JSONField(**kwargs)

    JSONModel._meta.database = database.database
    JSONModel.create_table(True)

    instance = JSONModel(data=value)
    instance.save()

    # Should be the same dict upon save.
    assert instance.data is value

    # Should be the same dict when queried.
    queried_instance = JSONModel.select().first()

    assert isinstance(queried_instance.data, dict_type)
    assert queried_instance.data == value
