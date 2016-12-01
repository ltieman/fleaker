# ~*~ coding: utf-8 ~*~
"""Collection of Marshmallow constants that can be used for saner defaults.

Example:
    These constants should be used as ``kwargs`` passed to the Marshmallow
    field. In Python 3, you can do multiple variables like this when defining
    a field.::

        class UserSchema(Schema):
            name = fields.String(**STR_REQUIRED)
            role = fields.Integer(**REQUIRED)

Attributes:
    REQUIRED (werkzeug.datastructures.ImmutableDict): This mixin can be passed
        to a Marshmallow field to make it required in a way that makes sense.
        This is because Marshmallow defines ``required`` as just the key being
        present and needs ``allow_none`` to not allow null values.
    STR_REQUIRED (werkzeug.datastructures.ImmutableDict): This is identical to
        ``REQUIRED`` except that it adds a check to make sure that the string
        is at least 1 character long.
"""

from marshmallow.validate import Length
from werkzeug.datastructures import ImmutableDict


REQUIRED = ImmutableDict({
    'required': True,
    'allow_none': False,
})
STR_REQUIRED = ImmutableDict({
    'required': True,
    'allow_none': False,
    'validate': Length(min=1),
})
