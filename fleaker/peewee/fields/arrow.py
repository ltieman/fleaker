# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.fields.arrow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom Peewee field that allows for datetimes to be :class:`arrow.Arrow`
objects without any additional conversion.

Example:
    This field can be used like any other Peewee field. All you need to do is
    add it as field to a model.

    .. code-block:: python

        import arrow
        import peewee

        from fleaker.peewee import ArrowDateTimeField

        class Event(peewee.Model):
            body = peewee.TextField()
            # This field can accept all the arguments that peewee.DateTimeField
            # can, which means you can set the default value to a callable.
            created = ArrowDateTimeField(default=arrow.utcnow)
            occured = ArrowDateTimeField()

        event = Event(
            # Field can be set with an instance of arrow.Arrow
            occured=arrow.utcnow(),
            body="Something important happened!"
        )

        assert isinstance(event.occured, arrow.Arrow)
        assert isinstance(event.created, arrow.Arrow)

        # This field can also be set with strings and dates
        event.created = arrow.utcnow().date()
        event.occured = '2016-12-13T02:09:48.075736+00:00'
        event.save()

        assert isinstance(event.occured, arrow.Arrow)
        assert isinstance(event.created, arrow.Arrow)


.. _Arrow: http://crsmithdev.com/arrow/
"""

from __future__ import absolute_import

import datetime

import arrow

from peewee import DateTimeField

from fleaker._compat import string_types


class ArrowDateTimeField(DateTimeField):
    """Peewee field that produces Arrow_ instances from Peewee fields.

    The big advantages to this are automatic timezone setting and that
    arrow is much nicer than the built in `datetime`

    .. _Arrow: http://crsmithdev.com/arrow/
    """

    def python_value(self, value):
        """Return the value in the data base as an arrow object.

        Returns:
            arrow.Arrow: An instance of arrow with the field filled in.
        """
        value = super(ArrowDateTimeField, self).python_value(value)

        if (isinstance(value, (datetime.datetime, datetime.date,
                               string_types))):
            return arrow.get(value)

        return value

    def db_value(self, value):
        """Convert the Arrow instance to a datetime for saving in the db."""
        if isinstance(value, string_types):
            value = arrow.get(value)

        if isinstance(value, arrow.Arrow):
            value = value.datetime

        return super(ArrowDateTimeField, self).db_value(value)
