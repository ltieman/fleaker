# ~*~ coding: utf-8 ~*~
"""
fleaker.marshmallow
~~~~~~~~~~~~~~~~~~~

Module that defines basic Marshmallow_ schema helpers and everything needed to
propery intialize Marshmallow.

Marshmallow_ is a lightweight serialization and deserialization library that
makes transforming submitted data very easy. It is quite useful for
transforming the input your API Routes get to what your models expect, and
vice versa. In addition to transforming input, it has a robut Validation
mechanism that can be used to automatically validate any data you work with.
Finally, by using a class based approach, all of your serialization,
deserialization, and validation is reusable!

Usage:::

    import arrow

    from fleaker import Schema
    from fleaker.marshmallow import ArrowField
    from marshmallow import fields, ValidationError


    class UserSchema(Schema):
        id = fields.Integer()
        name = fields.Str()
        signup_date = ArrowField()

    data = {
        'id': 1,
        'name': 'Tom',
        'signup_date': '2016-01-10T01:02:03Z'
    }

    schema = UserSchema()
    data = schema.load(data)
    assert data.id == 1
    assert data.name == 'Tom'
    assert data.signup_date == arrow.get('2016-01-10T01:02:03Z')

    # now a validation example!
    data = {
        'id': 'foo',
        'name': 1,
        'signup_date': 'bad ts',
    }

    try:
        schema.validate(data)
    except ValidationError:
        print("Something bad in the data!")

.. _Marshmallow: https://marshmallow.readthedocs.io/en/latest/
"""

from .constants import REQUIRED, STR_REQUIRED
from .extension import MarshmallowAwareApp, marsh
from .json_schema import FleakerJSONSchema
from .schema import Schema
from .fields import (
    ArrowField, ForeignKeyField, PendulumField, PhoneNumberField
)
