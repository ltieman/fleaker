"""Unit tests for the Peewee time mixins and fields."""

import datetime

import arrow
import peewee
import pendulum
import pytest

from fleaker.peewee.fields import ArrowDateTimeField, PendulumDateTimeField
from fleaker.peewee.mixins import (
    ArchivedMixin, CreatedMixin, CreatedModifiedMixin, ArrowArchivedMixin,
    ArrowCreatedMixin, ArrowCreatedModifiedMixin, PendulumArchivedMixin,
    PendulumCreatedMixin, PendulumCreatedModifiedMixin

)


@pytest.mark.parametrize('Mixin,dt', (
    (CreatedMixin, datetime.datetime),
    (ArrowCreatedMixin, arrow.Arrow),
    (PendulumCreatedMixin, pendulum.Pendulum),
))
def test_created_time_mixins(database, Mixin, dt):
    """Ensure that created time mixins work as expected."""
    class MixinTest(Mixin):
        class Meta:
            db_table = Mixin.__name__

    MixinTest._meta.database = database.database
    MixinTest.create_table(True)

    instance = MixinTest()
    instance.save()

    assert isinstance(instance.created, dt)


@pytest.mark.parametrize('Mixin,dt', (
    (CreatedModifiedMixin, datetime.datetime),
    (ArrowCreatedModifiedMixin, arrow.Arrow),
    (PendulumCreatedModifiedMixin, pendulum.Pendulum),
))
def test_created_modified_time_mixins(database, Mixin, dt):
    """Ensure that created and modified time mixins work as expected."""
    class MixinTest(Mixin):
        class Meta:
            db_table = Mixin.__name__

    MixinTest._meta.database = database.database
    MixinTest.create_table(True)

    instance = MixinTest()
    instance.save()

    og_created = instance.created

    assert isinstance(instance.created, dt)
    assert instance.modified is None

    instance.save()

    assert og_created is instance.created
    assert isinstance(instance.modified, dt)


@pytest.mark.parametrize('Mixin,dt', (
    (ArchivedMixin, datetime.datetime),
    (ArrowArchivedMixin, arrow.Arrow),
    (PendulumArchivedMixin, pendulum.Pendulum),
))
def test_archived_time_mixins(database, Mixin, dt):
    """Ensure that archived time mixins work as expected."""
    class MixinTest(Mixin):
        class Meta:
            db_table = Mixin.__name__

    MixinTest._meta.database = database.database
    MixinTest.create_table(True)

    instance = MixinTest()
    instance.save()
    klass = instance.__class__

    og_created = instance.created

    assert isinstance(instance.created, dt)
    assert instance.modified is None
    assert instance.archived is None

    instance.save()

    assert og_created is instance.created
    assert isinstance(instance.modified, dt)

    instance.archive_instance()

    assert isinstance(instance.archived, dt)
    assert instance.archived == instance.modified
    assert instance.is_archived

    with pytest.raises(peewee.DoesNotExist):
        klass.select().where(klass.is_archived == False).get()

    instance.unarchive_instance()

    assert instance.archived is None
    assert not instance.is_archived

    with pytest.raises(peewee.DoesNotExist):
        klass.select().where(klass.is_archived == True).get()


@pytest.mark.parametrize('Mixin,dt', (
    (CreatedMixin, datetime.datetime),
    (ArrowCreatedMixin, arrow.Arrow),
    (PendulumCreatedMixin, pendulum.Pendulum),
))
def test_timestamp_returned_properly(database, Mixin, dt):
    """Ensure that all time mixins return the right value from the DB."""
    class MixinTest(Mixin):
        class Meta:
            db_table = Mixin.__name__

    MixinTest._meta.database = database.database
    MixinTest.create_table(True)
    MixinTest().save()

    # Query the only instance and check that the returned value is correct.
    instance = MixinTest.select().first()

    assert isinstance(instance.created, dt)


@pytest.mark.parametrize('dt,Field', (
    (arrow.Arrow, ArrowDateTimeField),
    (pendulum.Pendulum, PendulumDateTimeField)
))
def test_time_python_value(database, dt, Field):
    """Ensure that the Python value is correctly handled for time fields."""
    field = Field()

    assert isinstance(field.python_value(datetime.datetime.utcnow()), dt)
    assert isinstance(
        field.python_value(datetime.datetime.utcnow().date()), dt
    )
    assert isinstance(
        field.python_value('2016-12-13T02:09:48.075736+00:00'), dt
    )
