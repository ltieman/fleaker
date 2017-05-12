# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.fields.pendulum
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom Peewee field that allows for datetimes to be :class:`pendulum.Pendulum`
objects without any additional conversion.

Example:
    This field can be used like any other Peewee field. All you need to do is
    add it as field to a model.

    .. code-block:: python

        import pendulum
        import peewee

        from fleaker.peewee import PendulumDateTimeField

        class Event(peewee.Model):
            body = peewee.TextField()
            # This field can accept all the arguments that peewee.DateTimeField
            # can, which means you can set the default value to a callable.
            created = PendulumDateTimeField(default=pendulum.utcnow)
            occured = PendulumDateTimeField()

        event = Event(
            # Field can be set with an instance of pendulum.Pendulum
            occured=pendulum.utcnow(),
            body="Something important happened!"
        )

        assert isinstance(event.occured, pendulum.Pendulum)
        assert isinstance(event.created, pendulum.Pendulum)

        # This field can also be set with strings and dates
        event.created = pendulum.utcnow().date()
        event.occured = '2016-12-13T02:09:48.075736+00:00'
        event.save()

        assert isinstance(event.occured, pendulum.Pendulum)
        assert isinstance(event.created, pendulum.Pendulum)


.. _Pendulum: https://pendulum.eustace.io/
"""

from __future__ import absolute_import

import datetime

import pendulum

from peewee import DateTimeField

from fleaker._compat import string_types


class PendulumDateTimeField(DateTimeField):
    """Peewee field that produces Pendulum_ instances from Peewee fields.

    The big advantages to this are automatic timezone setting and that
    Pendulum is much nicer than the built in `datetime`

    .. _Pendulum: https://pendulum.eustace.io/
    """

    def python_value(self, value):
        """Return the value in the database as an Pendulum object.

        Returns:
            pendulum.Pendulum:
                An instance of Pendulum with the field filled in.
        """
        value = super(PendulumDateTimeField, self).python_value(value)

        if isinstance(value, datetime.datetime):
            value = pendulum.instance(value)
        elif isinstance(value, datetime.date):
            value = pendulum.instance(
                datetime.datetime.combine(
                    value, datetime.datetime.min.time()
                )
            )
        elif isinstance(value, string_types):
            value = pendulum.parse(value)

        return value

    def db_value(self, value):
        """Convert the Pendulum instance to a datetime for saving in the db."""
        if isinstance(value, pendulum.Pendulum):
            value = datetime.datetime(
                value.year, value.month, value.day, value.hour, value.minute,
                value.second, value.microsecond, value.tzinfo
            )

        return super(PendulumDateTimeField, self).db_value(value)
