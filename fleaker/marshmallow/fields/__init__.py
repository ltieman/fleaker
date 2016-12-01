"""Module that defines custom Marshmallow fields."""

from .foreign_key import ForeignKeyField

# Arrow is optional
try:
    import arrow
except ImportError:
    pass
else:
    from .arrow import ArrowField

# Pendulum is optional
try:
    import pendulum
except ImportError:
    pass
else:
    from .pendulum import PendulumField

# Phonenumbers are optional
try:
    import phonenumbers
except ImportError:
    pass
else:
    from .phone_number import PhoneNumberField
