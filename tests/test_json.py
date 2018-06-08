# ~*~ coding: utf-8 ~*~
"""
tests.test_json
~~~~~~~~~~~~~~~

Unit tests for Fleaker.json module.
"""

import datetime
import decimal

from collections import OrderedDict

import arrow
import pendulum
import phonenumbers
import pytest

from fleaker._compat import text_type


@pytest.mark.parametrize('dt_mod', (pendulum, arrow))
def test_json_datetime_libs(app, dt_mod):
    """Ensure that datetime-like objects serialize properly."""
    if hasattr(dt_mod, 'utcnow'):
        data = {'now': dt_mod.utcnow()}
    elif hasattr(dt_mod, 'now'):
        data = {'now': dt_mod.now('UTC')}
    serialized = app.json.loads(app.json.dumps(data))

    for key in data:
        assert serialized[key] == text_type(data[key])


def test_json_decimal(app):
    """Ensure that decimal objects serialize properly."""
    data = {
        'regular': decimal.Decimal('2.01'),
        'trailing_zero': decimal.Decimal('2.0'),
        'trailing_zeros_with_number': decimal.Decimal('2.010'),
        'trailing_zeros': decimal.Decimal('2.000000'),
    }
    serialized = app.json.loads(app.json.dumps(data))

    assert serialized['regular'] == '2.01'
    assert serialized['trailing_zero'] == '2'
    assert serialized['trailing_zeros_with_number'] == '2.01'
    assert serialized['trailing_zeros'] == '2'


@pytest.mark.parametrize('now', (
    datetime.datetime.utcnow(),
    datetime.datetime.utcnow().date(),
))
def test_json_time(app, now):
    """Ensure that datetime.date objects serialize properly."""
    serialized = app.json.loads(app.json.dumps({'now': now}))
    assert serialized['now'] == now.isoformat()


def test_json_phonenumber(app):
    """Ensure that phonenumbers.PhoneNumber objects serialize properly."""
    data = {'tel': phonenumbers.parse("+13308286147")}
    serialized = app.json.loads(app.json.dumps(data))

    assert serialized['tel'] == '+13308286147'


def test_json_iterator(app):
    """Ensure that iterators serialize properly."""
    def test_iter():
        yield 1
        yield 2
        yield 3

    data = {'iter': test_iter()}
    serialized = app.json.loads(app.json.dumps(data))

    assert serialized['iter'] == [1, 2, 3]


def test_json_default(app):
    """Ensure that the JSON encoder can serialize common Python objects."""
    data = {
        'number': 1,
        'string': "This is a string.",
        'list_of_numbers': [1, 2, 3],
        'list_of_strings': ["This", "is", "a", "list", "o'", "strings"],
        'none': None,
    }
    serialized = app.json.loads(app.json.dumps(data))

    for key in data:
        assert serialized[key] == data[key]


def test_terrible_value(app):
    """Ensure that the custom JSON encoder errors out on some values."""
    with pytest.raises(TypeError):
        app.json.dumps({'obj': object})


def test_dump_nested_values(app):
    """Ensure that nested decimals can be dumped from OrderedDict."""
    data = OrderedDict([
        ('key', OrderedDict([
            ('nested_decimal', decimal.Decimal('1.12')),
        ])),
    ])

    assert app.json.dumps(data)
