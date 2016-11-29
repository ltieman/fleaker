"""Module that defines custom Marshmallow fields."""

from .foreign_key import ForeignKeyField

# Arrow is optional
try:
    import arrow
    from .arrow import ArrowField
except ImportError:
    pass

# Phonenumbers are optional
try:
    import phonenumbers
    from .phone_number import PhoneNumberField
except ImportError:
    pass
